"""
后台管理 API 视图
所有接口统一使用 permission_classes = [IsAuthenticated, IsSuperAdmin]
- 统计数据使用 Redis 缓存 5 分钟，以避免频繁聚合
- 操作审计日志由 apps.security.middleware.AuditLogMiddleware 自动记录

技能配置/题材模板/钩子库 直接对接 apps.skill.models 中的数据库表，
通过 SkillConfig.set_encrypted_value / get_decrypted_value 等方法加密存储。
"""
import secrets
import string
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsSuperAdmin
from apps.common.pagination import StandardPagination

from apps.users.models import User
from apps.membership.models import MembershipPlan, UserMembership, PromoCode
from apps.orders.models import Order, Payment

from apps.skill.models import SkillConfig, ThemeTemplate, HookLibrary

from .serializers import (
    # 用户
    AdminUserSerializer,
    UserToggleActiveResultSerializer,
    ResetPasswordSerializer,
    ResetPasswordResultSerializer,
    # 会员
    MembershipPlanSerializer,
    MembershipPlanCreateUpdateSerializer,
    PromoCodeGenerateSerializer,
    PromoCodeSerializer,
    PromoCodeGenerateResultSerializer,
    # 技能
    SkillConfigSerializer,
    SkillConfigUpdateSerializer,
    ThemeTemplateSerializer,
    HookSerializer,
    # 订单
    AdminOrderSerializer,
    OrderRefundResultSerializer,
    # Dashboard / 统计
    DashboardDataSerializer,
    StatsSummarySerializer,
    # 系统
    SystemSettingsSerializer,
    CacheClearResultSerializer,
)


# ============================================================
# 缓存 key 前缀与过期时间
# ============================================================
CACHE_KEY_DASHBOARD = "admin:dashboard:summary"
CACHE_KEY_STATS = "admin:stats:summary"
CACHE_KEY_SKILL_CONFIG_PREFIX = "admin:skill:config:"
CACHE_TTL = 60 * 5  # 5 分钟


# 敏感 key 关键词（命中则列表返回时 value 显示为 ******）
_SENSITIVE_KEY_TOKENS = ("api_key", "secret", "password", "token")


def _is_sensitive_key(key: str) -> bool:
    k = (key or "").lower()
    return any(tok in k for tok in _SENSITIVE_KEY_TOKENS)


# 取自 skill.services.SkillConfigService.DEFAULT_CONFIGS，保持与 skill 模块的默认配置一致，
# 避免在 admin_panel 中重复维护一份独立的默认配置列表。
# 注意：这里显式声明一份副本以避免引入循环依赖风险；若 skill/services.py 改动，
# 请同步更新此列表。
_DEFAULT_CONFIG_KEYS = [
    "llm.api_endpoint",
    "llm.api_key",
    "llm.temperature",
    "llm.max_tokens",
    "llm.model",
    "llm.enabled",
    "skill.version",
    "skill.active_nodes",
    "review.format_score_weight",
    "review.rhythm_score_weight",
    "review.content_score_weight",
    "review.production_score_weight",
    "review.pass_threshold",
    "export.default_format",
    "export.enable_watermark",
    "compliance.sensitive_words",
]


# ============================================================
# 通用工具
# ============================================================

def _random_password(length: int = 12) -> str:
    """生成包含大小写字母和数字的随机密码"""
    alphabet = string.ascii_letters + string.digits
    # 保证至少一个大写字母 + 一个小写字母 + 一个数字
    pwd = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    pwd += [secrets.choice(alphabet) for _ in range(length - 3)]
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)


def _ok(data=None, message: str = "success", code: int = 0,
        http_status: int = status.HTTP_200_OK):
    """统一响应包装"""
    return Response(
        {"code": code, "message": message, "data": data},
        status=http_status,
    )


def _fail(message: str, code: int = 400, http_status: int = status.HTTP_200_OK,
          data=None):
    return Response(
        {"code": code, "message": message, "data": data},
        status=http_status,
    )


# ============================================================
# Dashboard
# ============================================================

class DashboardView(APIView):
    """管理后台首页仪表盘

    核心指标 + 图表数据，缓存 5 分钟
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @staticmethod
    def _compute_dashboard():
        """计算仪表盘数据（未命中缓存时调用）"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # ---- 核心指标 ----
        total_users = User.objects.count()
        today_new_users = User.objects.filter(created_at__gte=today_start).count()
        total_members = (
            UserMembership.objects.filter(is_active=True, end_at__gt=now).count()
        )
        total_orders = Order.objects.count()
        total_revenue = (
            Order.objects.filter(status=Order.STATUS_PAID).aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        # 创作数：尝试从 creation.Script 等模型读取；若模型不存在则走 0
        total_creations = 0
        today_creations = 0
        try:
            from django.apps import apps as django_apps  # 本地别名
            # 兼容可能的创作模型：Script / Creation / Works 等
            candidate_models = [
                ("creation", "Script"),
                ("creation", "Creation"),
            ]
            for app_label, model_name in candidate_models:
                model_cls = django_apps.get_model(app_label, model_name, require_ready=False)
                total_creations = model_cls.objects.count()
                if hasattr(model_cls, "created_at"):
                    today_creations = model_cls.objects.filter(
                        created_at__gte=today_start
                    ).count()
                break
        except Exception:
            total_creations = 0
            today_creations = 0

        summary = {
            "total_users": total_users,
            "today_new_users": today_new_users,
            "total_members": total_members,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_creations": total_creations,
            "today_creations": today_creations,
        }

        # ---- 近 30 天用户增长折线图 ----
        user_growth_30d = []
        users_cumulative = User.objects.filter(created_at__lt=today_start - timedelta(days=29)).count()
        for i in range(29, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            new_count = User.objects.filter(
                created_at__gte=day_start, created_at__lt=day_end
            ).count()
            users_cumulative += new_count
            user_growth_30d.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "new_count": new_count,
                    "total_count": users_cumulative,
                }
            )

        # ---- 会员套餐占比饼图 ----
        plans = list(MembershipPlan.objects.all())
        total_members_count = max(
            UserMembership.objects.filter(is_active=True, end_at__gt=now).count(), 1
        )
        membership_share = []
        for plan in plans:
            member_count = UserMembership.objects.filter(
                plan=plan, is_active=True, end_at__gt=now
            ).count()
            membership_share.append(
                {
                    "plan_id": plan.id,
                    "plan_name": plan.name,
                    "member_count": member_count,
                    "percentage": round(member_count / total_members_count * 100, 2),
                }
            )

        # ---- 近 7 天创作数柱状图 ----
        creation_7d = []
        for i in range(6, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = 0
            try:
                from django.apps import apps as django_apps
                for app_label, model_name in [("creation", "Script"), ("creation", "Creation")]:
                    model_cls = django_apps.get_model(app_label, model_name, require_ready=False)
                    if hasattr(model_cls, "created_at"):
                        count = model_cls.objects.filter(
                            created_at__gte=day_start, created_at__lt=day_end
                        ).count()
                    break
            except Exception:
                count = 0
            creation_7d.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "count": count,
                }
            )

        return {
            "summary": summary,
            "user_growth_30d": user_growth_30d,
            "membership_share": membership_share,
            "creation_7d": creation_7d,
        }

    def get(self, request):
        cache_key = CACHE_KEY_DASHBOARD
        data = cache.get(cache_key)
        if not data:
            data = self._compute_dashboard()
            cache.set(cache_key, data, CACHE_TTL)
        serializer = DashboardDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return _ok(serializer.validated_data)


# ============================================================
# 用户管理
# ============================================================

class UserManagementViewSet(viewsets.GenericViewSet):
    """用户管理
    - list: GET /api/admin/users/?keyword=&is_active=&page=&page_size=
    - toggle_active: POST /api/admin/users/<id>/toggle_active/
    - reset_password: POST /api/admin/users/<id>/reset_password/
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = AdminUserSerializer
    pagination_class = StandardPagination
    lookup_field = "pk"

    def _base_queryset(self):
        qs = User.objects.all().order_by("-created_at")
        keyword = self.request.query_params.get("keyword", "").strip()
        is_active = self.request.query_params.get("is_active")
        if keyword:
            qs = qs.filter(
                Q(nickname__icontains=keyword)
                | Q(phone__icontains=keyword)
                | Q(email__icontains=keyword)
            )
        if is_active in ("true", "1", "True"):
            qs = qs.filter(is_active=True)
        elif is_active in ("false", "0", "False"):
            qs = qs.filter(is_active=False)
        return qs

    def list(self, request, *args, **kwargs):
        qs = self._base_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return _ok(serializer.data)

    @action(detail=True, methods=["post"], url_path="toggle_active")
    def toggle_active(self, request, pk=None):
        """启用/禁用用户（切换 is_active）"""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return _fail("用户不存在")
        # 不允许禁用自己或其他超级管理员（自我保护）
        if user == request.user or user.is_superuser:
            return _fail("不能禁用超级管理员或当前账号")
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        # 清除该用户相关缓存（登录态等）
        cache.delete_pattern(f"auth:user:{user.pk}:*")
        data = {
            "user_id": user.pk,
            "is_active": user.is_active,
            "message": "已启用" if user.is_active else "已禁用",
        }
        serializer = UserToggleActiveResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 清除 dashboard 缓存
        cache.delete(CACHE_KEY_DASHBOARD)
        return _ok(serializer.validated_data)

    @action(detail=True, methods=["post"], url_path="reset_password")
    def reset_password(self, request, pk=None):
        """重置密码：接受 new_password；为空则由后端自动生成 12 位随机密码"""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return _fail("用户不存在")

        input_ser = ResetPasswordSerializer(data=request.data or {})
        input_ser.is_valid(raise_exception=True)
        new_password = input_ser.validated_data.get("new_password") or _random_password(12)

        user.password = make_password(new_password)
        user.save(update_fields=["password"])

        data = {
            "user_id": user.pk,
            "new_password": new_password,
            "message": "密码已重置",
        }
        serializer = ResetPasswordResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return _ok(serializer.validated_data)


# ============================================================
# 会员管理
# ============================================================

class MembershipPlanViewSet(viewsets.ModelViewSet):
    """会员套餐管理：列表 / 新增 / 更新
    - 软删除（实际仅禁用）可以通过 PUT is_active=False 实现
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        return MembershipPlan.objects.all().order_by("sort_order", "-created_at")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return MembershipPlanCreateUpdateSerializer
        return MembershipPlanSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        cache.delete(CACHE_KEY_DASHBOARD)
        return _ok(serializer.data, message="套餐已创建", http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.get("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        cache.delete(CACHE_KEY_DASHBOARD)
        return _ok(serializer.data, message="套餐已更新")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if UserMembership.objects.filter(plan=instance).exists():
            return _fail("已有会员使用此套餐，无法删除；可将 is_active 设置为 False 以停用")
        instance.delete()
        cache.delete(CACHE_KEY_DASHBOARD)
        return _ok(None, message="套餐已删除")


class PromoCodeGenerateView(APIView):
    """批量生成卡密"""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @transaction.atomic
    def post(self, request):
        input_ser = PromoCodeGenerateSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        data = input_ser.validated_data
        try:
            plan = MembershipPlan.objects.get(pk=data["plan_id"])
        except MembershipPlan.DoesNotExist:
            return _fail("套餐不存在")

        count = int(data["count"])
        valid_days = int(data["valid_days"])
        max_uses = int(data["max_uses_per_code"])
        expires_at = timezone.now() + timedelta(days=valid_days)

        created = []
        existing_codes = set(
            PromoCode.objects.values_list("code", flat=True)
        )
        for _ in range(count):
            while True:
                code = secrets.token_urlsafe(8).replace("-", "").replace("_", "").upper()[:16]
                # 确保唯一
                if code not in existing_codes:
                    existing_codes.add(code)
                    break
            created.append(
                PromoCode(
                    code=code,
                    plan=plan,
                    max_uses=max_uses,
                    used_count=0,
                    expires_at=expires_at,
                    is_active=True,
                )
            )
        PromoCode.objects.bulk_create(created, batch_size=200)

        codes_ser = PromoCodeSerializer(created, many=True)
        result = {
            "plan_id": plan.pk,
            "plan_name": plan.name,
            "generated_count": len(created),
            "codes": codes_ser.data,
        }
        return _ok(result, message=f"已生成 {len(created)} 张卡密")


# ============================================================
# 技能配置管理（对接 apps.skill.models.SkillConfig）
# ============================================================

class SkillConfigView(APIView):
    """技能配置管理（对接 apps.skill.models.SkillConfig 表）

    - GET  /api/admin/skill/configs/           列出全部配置（含默认列表；敏感项 value 显示为 ******）
    - GET  /api/admin/skill/configs/<key>/     查询单条配置（明文，仅超级管理员可用）
    - PUT  /api/admin/skill/configs/<key>/     更新/新增某条配置（明文 -> set_encrypted_value 加密存储）
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def _get_default_configs(self):
        """返回 skill 模块默认配置的 key 集合（用于补充 DB 中尚无记录的 key）"""
        return set(_DEFAULT_CONFIG_KEYS)

    def get(self, request, key=None):
        # 单条查询
        if key:
            obj = SkillConfig.objects.filter(config_key=key).first()
            if obj is None:
                return _fail(f"配置项 {key} 不存在")
            plain = obj.get_decrypted_value() or ""
            # 单条查询不做脱敏，保证管理员能看到完整明文（前端可按需自行遮盖）
            data = {
                "key": obj.config_key,
                "value": plain,
                "description": obj.description or "",
                "updated_at": obj.updated_at,
            }
            serializer = SkillConfigSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return _ok(serializer.validated_data)

        # 列表查询：DB 记录 + 默认列表中尚未落库的 key，合并后统一返回
        db_map = {}
        for sc in SkillConfig.objects.all():
            plain = sc.get_decrypted_value() or ""
            db_map[sc.config_key] = {
                "key": sc.config_key,
                "value": plain,
                "description": sc.description or "",
                "updated_at": sc.updated_at,
            }

        all_keys = set(db_map.keys()) | self._get_default_configs()
        items = []
        for k in sorted(all_keys):
            base = db_map.get(k, {
                "key": k,
                "value": "",
                "description": "",
                "updated_at": None,
            })
            # 敏感项：列表显示时遮盖为 ******
            display_value = "******" if _is_sensitive_key(k) else base.get("value", "")
            items.append({
                "key": base["key"],
                "value": display_value,
                "description": base.get("description", ""),
                "updated_at": base.get("updated_at"),
            })

        serializer = SkillConfigSerializer(items, many=True)
        return _ok(serializer.data)

    def put(self, request, key=None):
        if not key:
            return _fail("请在 URL 中提供配置 key")
        input_ser = SkillConfigUpdateSerializer(data=request.data or {})
        input_ser.is_valid(raise_exception=True)
        new_value = input_ser.validated_data.get("value", "")
        new_description = input_ser.validated_data.get("description", "")

        # 通过 SkillConfig.set_encrypted_value 加密存储（与 skill 模块加密实现一致）
        obj, created = SkillConfig.objects.update_or_create(
            config_key=key,
            defaults={
                "description": new_description or key,
            },
        )
        obj.set_encrypted_value(str(new_value))
        obj.save()

        # 清除 skill 模块相关的缓存前缀，让下游读取生效
        try:
            cache.delete_pattern("skill:config:*")
        except Exception:
            pass
        cache.delete(CACHE_KEY_DASHBOARD)
        cache.delete(CACHE_KEY_STATS)

        data = {
            "key": obj.config_key,
            "value": new_value,
            "description": obj.description,
            "updated_at": obj.updated_at,
        }
        return _ok(data, message="配置已更新")


# ============================================================
# 题材模板管理（对接 apps.skill.models.ThemeTemplate）
# ============================================================

class ThemeTemplateView(APIView):
    """题材模板：列表 / 新增（对接 apps.skill.models.ThemeTemplate 表）"""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        qs = ThemeTemplate.objects.all().order_by("sort_order", "-created_at")
        items = []
        for t in qs:
            # 字段映射：将 ThemeTemplate 表字段映射为前端期望的字段
            prompt = ""
            try:
                params = t.params or {}
                hook_types = params.get("hook_types") if isinstance(params, dict) else []
                if hook_types and isinstance(hook_types, list):
                    prompt = ",".join(str(x) for x in hook_types)
            except Exception:
                prompt = ""

            items.append({
                "id": str(t.id),
                "name": t.theme_name or "",
                "category": t.theme_code or "",
                "prompt_template": prompt,
                "is_active": bool(t.is_active),
                "sort_order": int(t.sort_order or 0),
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            })
        serializer = ThemeTemplateSerializer(items, many=True)
        return _ok(serializer.data)

    def post(self, request):
        serializer = ThemeTemplateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        theme_code = v.get("category") or f"custom-{secrets.token_hex(6)}"
        theme_name = v.get("name")
        if not theme_name:
            return _fail("题材名称不能为空")

        obj = ThemeTemplate.objects.create(
            theme_code=theme_code,
            theme_name=theme_name,
            is_active=bool(v.get("is_active", True)),
            sort_order=int(v.get("sort_order", 0) or 0),
            description="",
        )
        cache.delete(CACHE_KEY_DASHBOARD)

        data = {
            "id": str(obj.id),
            "name": obj.theme_name,
            "category": obj.theme_code,
            "prompt_template": "",
            "is_active": bool(obj.is_active),
            "sort_order": obj.sort_order,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        return _ok(data, message="题材已创建", http_status=status.HTTP_201_CREATED)


class ThemeTemplateDetailView(APIView):
    """题材模板更新（对接 apps.skill.models.ThemeTemplate 表）"""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def put(self, request, theme_id=None):
        try:
            obj = ThemeTemplate.objects.get(pk=theme_id)
        except ThemeTemplate.DoesNotExist:
            return _fail("题材不存在")

        serializer = ThemeTemplateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        obj.theme_name = v.get("name", obj.theme_name)
        obj.theme_code = v.get("category", obj.theme_code)
        obj.is_active = bool(v.get("is_active", obj.is_active))
        obj.sort_order = int(v.get("sort_order", obj.sort_order) or 0)
        obj.save()

        data = {
            "id": str(obj.id),
            "name": obj.theme_name,
            "category": obj.theme_code,
            "prompt_template": "",
            "is_active": bool(obj.is_active),
            "sort_order": obj.sort_order,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        return _ok(data, message="题材已更新")


# ============================================================
# 钩子库管理（对接 apps.skill.models.HookLibrary）
# ============================================================

class HookView(APIView):
    """钩子库：列表 / 新增（对接 apps.skill.models.HookLibrary 表）"""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        qs = HookLibrary.objects.all().order_by("-use_count", "-created_at")
        items = []
        for h in qs:
            snippet = (h.content or "")[:20]
            items.append({
                "id": str(h.id),
                "name": snippet + ("..." if len(h.content or "") > 20 else ""),
                "hook_type": h.hook_type or "opening",
                "content": h.content or "",
                "is_active": bool(h.is_active),
                "created_at": h.created_at,
            })
        serializer = HookSerializer(items, many=True)
        return _ok(serializer.data)

    def post(self, request):
        serializer = HookSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        content = v.get("content")
        if not content:
            return _fail("钩子内容不能为空")

        obj = HookLibrary.objects.create(
            hook_type=v.get("hook_type", "opening"),
            content=content,
            tags="",
            is_active=bool(v.get("is_active", True)),
        )

        snippet = (obj.content or "")[:20]
        data = {
            "id": str(obj.id),
            "name": snippet + ("..." if len(obj.content or "") > 20 else ""),
            "hook_type": obj.hook_type,
            "content": obj.content,
            "is_active": bool(obj.is_active),
            "created_at": obj.created_at,
        }
        return _ok(data, message="钩子已创建", http_status=status.HTTP_201_CREATED)


# ============================================================
# 订单管理
# ============================================================

class OrderManagementViewSet(viewsets.GenericViewSet):
    """订单管理

    - list: GET /api/admin/orders/?status=&keyword=&page=&page_size=
    - refund: POST /api/admin/orders/<id>/refund/
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = AdminOrderSerializer
    pagination_class = StandardPagination

    def _base_queryset(self):
        qs = (
            Order.objects.select_related("user", "membership_plan")
            .all()
            .order_by("-created_at")
        )
        status_filter = self.request.query_params.get("status")
        keyword = self.request.query_params.get("keyword", "").strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        if keyword:
            qs = qs.filter(
                Q(order_no__icontains=keyword)
                | Q(user__nickname__icontains=keyword)
                | Q(user__phone__icontains=keyword)
            )
        return qs

    def list(self, request, *args, **kwargs):
        qs = self._base_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return _ok(serializer.data)

    @action(detail=True, methods=["post"], url_path="refund")
    def refund(self, request, pk=None):
        """退款：将订单状态置为 refunded；同时尝试扣减对应会员剩余天数"""
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return _fail("订单不存在")

        if order.status == Order.STATUS_REFUNDED:
            return _fail("该订单已经退款")
        if order.status not in (Order.STATUS_PAID,):
            return _fail("仅能对已支付订单执行退款")

        with transaction.atomic():
            order.status = Order.STATUS_REFUNDED
            order.save(update_fields=["status"])

            # 若订单关联了会员套餐，尝试扣减会员
            if order.membership_plan:
                # 找到该用户使用本订单开通（或最新开通）的一条会员记录扣减
                m = (
                    UserMembership.objects.filter(
                        user=order.user, plan=order.membership_plan, is_active=True
                    )
                    .order_by("-created_at")
                    .first()
                )
                if m:
                    # 将有效期截断到当前时间（等效于撤销本次开通的剩余权益）
                    m.end_at = timezone.now()
                    m.is_active = False
                    m.save(update_fields=["end_at", "is_active"])

        cache.delete(CACHE_KEY_DASHBOARD)
        data = {
            "order_id": order.pk,
            "order_no": order.order_no,
            "success": True,
            "message": "退款成功",
        }
        serializer = OrderRefundResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return _ok(serializer.validated_data)


# ============================================================
# 统计总览
# ============================================================

class StatsSummaryView(APIView):
    """统计总览（比 dashboard 更细粒度的统计数据）

    包含订单分状态统计、会员分套餐统计等；缓存 5 分钟
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def _compute(self):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_users = User.objects.count()
        today_new_users = User.objects.filter(created_at__gte=today_start).count()
        total_members = UserMembership.objects.filter(
            is_active=True, end_at__gt=now
        ).count()

        orders = Order.objects
        total_orders = orders.count()
        paid_orders = orders.filter(status=Order.STATUS_PAID).count()
        pending_orders = orders.filter(status=Order.STATUS_PENDING).count()
        refunded_orders = orders.filter(status=Order.STATUS_REFUNDED).count()
        total_revenue = orders.filter(status=Order.STATUS_PAID).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

        # 创作数
        total_creations = 0
        today_creations = 0
        try:
            from django.apps import apps as django_apps
            for app_label, model_name in [("creation", "Script"), ("creation", "Creation")]:
                model_cls = django_apps.get_model(app_label, model_name, require_ready=False)
                total_creations = model_cls.objects.count()
                if hasattr(model_cls, "created_at"):
                    today_creations = model_cls.objects.filter(
                        created_at__gte=today_start
                    ).count()
                break
        except Exception:
            total_creations = 0
            today_creations = 0

        summary = {
            "users": {
                "total_users": total_users,
                "today_new_users": today_new_users,
                "total_members": total_members,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "total_creations": total_creations,
                "today_creations": today_creations,
            },
            "orders": {
                "total": total_orders,
                "paid": paid_orders,
                "pending": pending_orders,
                "refunded": refunded_orders,
                "total_revenue": str(total_revenue),
            },
            "members": {
                "total_active": total_members,
                "plans": [
                    {
                        "plan_id": p.id,
                        "plan_name": p.name,
                        "member_count": UserMembership.objects.filter(
                            plan=p, is_active=True, end_at__gt=now
                        ).count(),
                    }
                    for p in MembershipPlan.objects.all()
                ],
            },
            "creations": {
                "total": total_creations,
                "today": today_creations,
            },
            "cache_hit_rate": 0.0,
        }
        return summary

    def get(self, request):
        data = cache.get(CACHE_KEY_STATS)
        if not data:
            data = self._compute()
            cache.set(CACHE_KEY_STATS, data, CACHE_TTL)
        serializer = StatsSummarySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return _ok(serializer.validated_data)


# ============================================================
# 系统设置与缓存
# ============================================================

class SystemSettingsView(APIView):
    """系统设置（只读快照）"""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        data = {
            "site_name": getattr(settings, "SITE_NAME", "ScriptForge 短剧创作平台"),
            "support_email": getattr(settings, "SUPPORT_EMAIL", "support@scriptforge.local"),
            "cache_backend": getattr(settings, "CACHES", {}).get("default", {}).get("BACKEND", ""),
            "time_zone": getattr(settings, "TIME_ZONE", "Asia/Shanghai"),
            "debug_mode": bool(getattr(settings, "DEBUG", False)),
            "api_rate_limit_per_hour": int(
                getattr(settings, "DEFAULT_THROTTLE_RATES", {}).get("user", "1000/hour").split("/")[0]
            ),
        }
        serializer = SystemSettingsSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return _ok(serializer.validated_data)


class CacheClearView(APIView):
    """清除缓存（admin 命名空间 + dashboard/skill 相关 key）"""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        # 精确清除我们管理的 key；不直接调用 cache.clear() 以免误伤用户登录态
        cleared = 0
        targets = [
            CACHE_KEY_DASHBOARD,
            CACHE_KEY_STATS,
        ]
        for k in targets:
            if cache.delete(k):
                cleared += 1
        # 前缀匹配
        try:
            # cache.delete_pattern 由 django-redis 提供；若后端不支持则静默跳过
            cleared += cache.delete_pattern(CACHE_KEY_SKILL_CONFIG_PREFIX + "*") or 0
            cleared += cache.delete_pattern("admin:*") or 0
            cleared += cache.delete_pattern("skill:config:*") or 0
        except Exception:
            pass

        data = {
            "success": True,
            "message": "缓存已清除",
            "cleared_keys": int(cleared),
        }
        serializer = CacheClearResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return _ok(serializer.validated_data)
