# -*- coding: utf-8 -*-
"""后台 API — 配置中心 — 系统配置与题材钩子"""
import secrets
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
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.pagination import StandardPagination
from apps.console.responses import (
    CACHE_KEY_DASHBOARD,
    CACHE_KEY_DASHBOARD_LEGACY,
    CACHE_KEY_STATS,
    CACHE_KEY_SKILL_CONFIG_PREFIX,
    CACHE_TTL,
    DEFAULT_CONFIG_KEYS,
    api_fail,
    _is_sensitive_key,
    api_ok,
    _random_password)

from apps.skill.models import HookLibrary, SkillConfig, ThemeTemplate
from apps.console.serializers import (
    HookSerializer,
    SkillConfigSerializer,
    SkillConfigUpdateSerializer,
    ThemeTemplateSerializer,
)


# ============================================================
# 技能配置管理（对接 apps.skill.models.SkillConfig）
# ============================================================

class SkillConfigView(APIView):
    """技能配置管理（对接 apps.skill.models.SkillConfig 表）

    - GET  /api/admin/portal/configs/           列出全部配置（含默认列表；敏感项 value 显示为 ******）
    - GET  /api/admin/portal/configs/<key>/     查询单条配置（明文，仅超级管理员可用）
    - PUT  /api/admin/portal/configs/<key>/     更新/新增某条配置（明文 -> set_encrypted_value 加密存储）
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_default_configs(self):
        """返回 skill 模块默认配置的 key 集合（用于补充 DB 中尚无记录的 key）"""
        return set(DEFAULT_CONFIG_KEYS)

    def get(self, request, key=None):
        # 单条查询
        if key:
            obj = SkillConfig.objects.filter(config_key=key).first()
            if obj is None:
                return api_fail(f"配置项 {key} 不存在")
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
            return api_ok(serializer.validated_data)

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
        return api_ok(serializer.data)

    def put(self, request, key=None):
        if not key:
            return api_fail("请在 URL 中提供配置 key")
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
        return api_ok(data, message="配置已更新")


class CreationFormCatalogView(APIView):
    """C 端创作表单 catalog：读取 SSOT + 运营覆盖，PUT 保存覆盖到 SkillConfig。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from apps.workflow.fusion.ssot_catalog import FusionSsotCatalog, get_creation_form_overrides

        base = FusionSsotCatalog().public_catalog()
        overrides = get_creation_form_overrides()
        return api_ok(
            {
                "skillVersion": base.get("skillVersion"),
                "catalog": {
                    "budgetLevels": base.get("budgetLevels") or [],
                    "platforms": base.get("platforms") or [],
                    "creationEntries": base.get("creationEntries") or [],
                    "formatVariants": base.get("formatVariants") or [],
                    "episodeSettings": base.get("episodeSettings") or {},
                    "sections": base.get("sections") or {},
                    "themes": base.get("themes") or [],
                    "creationEntryProfiles": base.get("creationEntryProfiles") or {},
                },
                "overrides": overrides,
            }
        )

    def put(self, request):
        from apps.workflow.fusion.ssot_catalog import get_creation_form_overrides

        payload = request.data or {}
        overrides = payload.get("overrides")
        if overrides is None:
            overrides = payload

        if not isinstance(overrides, dict):
            return api_fail("overrides 必须是 JSON 对象")

        allowed_keys = {
            "budgetLevels",
            "platforms",
            "creationEntries",
            "formatVariants",
            "episodeSettings",
            "sections",
            "themes",
            "creationEntryProfiles",
        }
        cleaned = {k: v for k, v in overrides.items() if k in allowed_keys}
        if not cleaned and overrides:
            return api_fail(f"仅允许覆盖字段：{', '.join(sorted(allowed_keys))}")

        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        CreationFormOverrideService.save_overrides(cleaned)
        try:
            cache.delete_pattern("skill:config:*")
        except Exception:
            pass

        merged = get_creation_form_overrides()
        return api_ok({"overrides": merged}, message="创作表单配置已保存")


class CreationFormImportView(APIView):
    """POST /api/admin/portal/creation-form/import/ — 从磁盘 project-config 同步入口 profile。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        from apps.skill.config.portal.creation_form import CreationFormOverrideService
        from apps.workflow.fusion.ssot_catalog import FusionSsotCatalog, get_creation_form_overrides

        payload = request.data if isinstance(request.data, dict) else {}
        mode = str(payload.get("mode") or "sync").strip().lower()
        overwrite = bool(payload.get("overwrite", False))

        if mode == "import":
            ok = CreationFormOverrideService.import_catalog_from_disk(overwrite=overwrite)
        else:
            ok = CreationFormOverrideService.sync_catalog_from_disk()

        if not ok:
            return api_fail("磁盘 catalog 为空或导入被跳过")

        from apps.skill.config.portal.reference_libs import ReferenceLibraryService
        from apps.skill.config.portal.review_scoring import ReviewScoringService
        from apps.skill.config.portal.theme_templates import ThemeTemplateCatalogService

        ref_count = ReferenceLibraryService.import_from_disk(overwrite=overwrite)
        theme_count = ThemeTemplateCatalogService.import_from_disk(merge=True)
        ReviewScoringService.import_thresholds_from_disk()

        base = FusionSsotCatalog().public_catalog()
        return api_ok(
            {
                "skillVersion": base.get("skillVersion"),
                "catalog": {
                    "creationEntryProfiles": base.get("creationEntryProfiles") or {},
                },
                "overrides": get_creation_form_overrides(),
                "referenceFilesImported": ref_count,
                "themeTemplatesMerged": theme_count,
            },
            message="已从磁盘同步创作表单 catalog",
        )


# ============================================================
# 题材模板管理（对接 apps.skill.models.ThemeTemplate）
# ============================================================

class ThemeTemplateView(APIView):
    """题材模板：列表 / 新增（对接 apps.skill.models.ThemeTemplate 表）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

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
        return api_ok(serializer.data)

    def post(self, request):
        serializer = ThemeTemplateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        theme_code = v.get("category") or f"custom-{secrets.token_hex(6)}"
        theme_name = v.get("name")
        if not theme_name:
            return api_fail("题材名称不能为空")

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
        return api_ok(data, message="题材已创建", http_status=status.HTTP_201_CREATED)


class ThemeTemplateDetailView(APIView):
    """题材模板更新（对接 apps.skill.models.ThemeTemplate 表）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, theme_id=None):
        try:
            obj = ThemeTemplate.objects.get(pk=theme_id)
        except ThemeTemplate.DoesNotExist:
            return api_fail("题材不存在")

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
        return api_ok(data, message="题材已更新")


# ============================================================
# 钩子库管理（对接 apps.skill.models.HookLibrary）
# ============================================================

class HookView(APIView):
    """钩子库：列表 / 新增（对接 apps.skill.models.HookLibrary 表）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

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
                "use_count": h.use_count,
                "created_at": h.created_at,
            })
        serializer = HookSerializer(items, many=True)
        return api_ok(serializer.data)

    def post(self, request):
        serializer = HookSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        content = v.get("content")
        if not content:
            return api_fail("钩子内容不能为空")

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
        return api_ok(data, message="钩子已创建", http_status=status.HTTP_201_CREATED)


class HookDetailView(APIView):
    """钩子库：更新 / 删除"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, hook_id=None):
        try:
            obj = HookLibrary.objects.get(pk=hook_id)
        except HookLibrary.DoesNotExist:
            return api_fail("钩子不存在")

        serializer = HookSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        if v.get("content"):
            obj.content = v["content"]
        if v.get("hook_type"):
            obj.hook_type = v["hook_type"]
        if "is_active" in v:
            obj.is_active = bool(v["is_active"])
        obj.save()

        snippet = (obj.content or "")[:20]
        data = {
            "id": str(obj.id),
            "name": snippet + ("..." if len(obj.content or "") > 20 else ""),
            "hook_type": obj.hook_type,
            "content": obj.content,
            "is_active": bool(obj.is_active),
            "use_count": obj.use_count,
            "created_at": obj.created_at,
        }
        return api_ok(data, message="钩子已更新")

    def delete(self, request, hook_id=None):
        try:
            obj = HookLibrary.objects.get(pk=hook_id)
        except HookLibrary.DoesNotExist:
            return api_fail("钩子不存在")
        obj.delete()
        return api_ok(None, message="钩子已删除")
