"""
后台管理面板序列化器
"""
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.users.models import User, UserProfile
from apps.membership.models import MembershipPlan, UserMembership, PromoCode
from apps.orders.models import Order, Payment


# ============================================================
# 通用辅助：Skill 配置加解密（与 base 模块中的加解密保持兼容）
# ============================================================

def _skill_encrypt(plain: str) -> str:
    """使用 SKILL_ENCRYPT_KEY AES-256-CBC 加密字符串，返回 base64(iv+ciphertext)"""
    if plain in (None, ""):
        return ""
    key = hashlib.sha256(str(getattr(settings, "SKILL_ENCRYPT_KEY", "")).encode("utf-8")).digest()
    iv = hashlib.sha256(timezone.now().isoformat().encode("utf-8")).digest()[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(str(plain).encode("utf-8"), AES.block_size))
    return base64.b64encode(iv + ct_bytes).decode("ascii")


def _skill_decrypt(cipher_b64: str) -> str:
    """解密 AES-256-CBC 字符串；解密失败返回原值（兼容未加密数据）"""
    if cipher_b64 in (None, ""):
        return ""
    try:
        key = hashlib.sha256(str(getattr(settings, "SKILL_ENCRYPT_KEY", "")).encode("utf-8")).digest()
        raw = base64.b64decode(str(cipher_b64).encode("ascii"))
        iv = raw[:16]
        ct = raw[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size).decode("utf-8")
    except Exception:
        return str(cipher_b64)


# ============================================================
# 用户管理
# ============================================================

class AdminUserSerializer(serializers.ModelSerializer):
    """后台用户列表序列化器"""

    user_id = serializers.UUIDField(source="id", read_only=True)
    phone = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    nickname = serializers.CharField(read_only=True)
    is_member = serializers.SerializerMethodField()
    current_plan = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "user_id",
            "phone",
            "email",
            "nickname",
            "is_active",
            "is_superuser",
            "is_member",
            "current_plan",
            "order_count",
            "created_at",
        ]

    def get_is_member(self, obj) -> bool:
        return (
            UserMembership.objects.filter(
                user=obj, is_active=True, end_at__gt=timezone.now()
            ).exists()
        )

    def get_current_plan(self, obj) -> str:
        m = (
            UserMembership.objects.filter(
                user=obj, is_active=True, end_at__gt=timezone.now()
            )
            .select_related("plan")
            .first()
        )
        return m.plan.name if m else ""

    def get_order_count(self, obj) -> int:
        return Order.objects.filter(user=obj).count()


class UserToggleActiveResultSerializer(serializers.Serializer):
    """用户启用/禁用结果"""

    user_id = serializers.UUIDField()
    is_active = serializers.BooleanField()
    message = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    """重置密码输入：若前端不传密码，则由后端生成 12 位随机密码"""

    new_password = serializers.CharField(
        max_length=128,
        required=False,
        allow_blank=True,
        help_text="可选；若为空将由后端自动生成随机密码",
    )

    def validate_new_password(self, value):
        if not value:
            return value
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages)) from e
        return value


class ResetPasswordResultSerializer(serializers.Serializer):
    """重置密码返回（明文密码仅在本次响应返回一次）"""

    user_id = serializers.UUIDField()
    new_password = serializers.CharField()
    message = serializers.CharField()


# ============================================================
# 会员管理
# ============================================================

class MembershipPlanBaseSerializer(serializers.ModelSerializer):
    """会员套餐 - 基础字段"""

    class Meta:
        model = MembershipPlan
        fields = [
            "id",
            "name",
            "price",
            "validity_days",
            "creation_quota",
            "features",
            "is_active",
            "is_recommended",
            "sort_order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MembershipPlanSerializer(MembershipPlanBaseSerializer):
    """会员套餐 - 列表/详情展示"""

    member_count = serializers.SerializerMethodField()

    class Meta(MembershipPlanBaseSerializer.Meta):
        fields = MembershipPlanBaseSerializer.Meta.fields + ["member_count"]

    def get_member_count(self, obj) -> int:
        return UserMembership.objects.filter(plan=obj, is_active=True).count()


class MembershipPlanCreateUpdateSerializer(MembershipPlanBaseSerializer):
    """套餐新增/更新输入"""

    def validate_price(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError("价格不能为负数")
        return value

    def validate_validity_days(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("有效期必须大于 0")
        return value


class PromoCodeGenerateSerializer(serializers.Serializer):
    """批量生成卡密输入"""

    plan_id = serializers.UUIDField(help_text="套餐 ID")
    count = serializers.IntegerField(
        min_value=1, max_value=1000, default=10, help_text="生成数量（1-1000）"
    )
    valid_days = serializers.IntegerField(
        min_value=1, max_value=3650, default=365, help_text="有效天数（1-3650）"
    )
    max_uses_per_code = serializers.IntegerField(
        min_value=1, max_value=1000, default=1, help_text="单码最大使用次数"
    )


class PromoCodeSerializer(serializers.ModelSerializer):
    """卡密详情"""

    plan_name = serializers.CharField(source="plan.name", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = PromoCode
        fields = [
            "id",
            "code",
            "plan",
            "plan_name",
            "max_uses",
            "used_count",
            "expires_at",
            "is_active",
            "is_expired",
            "is_available",
            "created_at",
        ]


class PromoCodeGenerateResultSerializer(serializers.Serializer):
    """批量生成卡密返回"""

    plan_id = serializers.UUIDField()
    plan_name = serializers.CharField()
    generated_count = serializers.IntegerField()
    codes = PromoCodeSerializer(many=True)


# ============================================================
# 技能配置管理
# ============================================================

class SkillConfigSerializer(serializers.Serializer):
    """技能配置键值对（key -> 明文 value）
    - GET 时自动解密返回明文给前端
    - PUT/POST 时由前端传明文，视图层加密后存储
    """

    key = serializers.CharField(max_length=100)
    value = serializers.CharField(allow_blank=True, help_text="明文配置值；保存时会自动加密")
    description = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )
    updated_at = serializers.DateTimeField(required=False, allow_null=True)


class SkillConfigUpdateSerializer(serializers.Serializer):
    """技能配置更新输入（前端传明文）"""

    value = serializers.CharField(required=True, allow_blank=True)
    description = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )


class ThemeTemplateSerializer(serializers.Serializer):
    """题材模板"""

    id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(max_length=100)
    category = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    prompt_template = serializers.CharField(
        required=False, allow_blank=True, default="", help_text="题材对应的创作提示词模板"
    )
    is_active = serializers.BooleanField(required=False, default=True)
    sort_order = serializers.IntegerField(required=False, default=0)
    created_at = serializers.DateTimeField(required=False, read_only=True)
    updated_at = serializers.DateTimeField(required=False, read_only=True)


class HookSerializer(serializers.Serializer):
    """钩子库"""

    id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(max_length=100)
    hook_type = serializers.CharField(
        max_length=32, default="common", help_text="钩子类型：common / opening / ending / conflict"
    )
    content = serializers.CharField(help_text="钩子正文内容")
    is_active = serializers.BooleanField(required=False, default=True)
    created_at = serializers.DateTimeField(required=False, read_only=True)


# ============================================================
# 订单管理
# ============================================================

class AdminOrderSerializer(serializers.ModelSerializer):
    """后台订单列表"""

    user_phone = serializers.CharField(source="user.phone", read_only=True)
    user_nickname = serializers.CharField(source="user.nickname", read_only=True)
    plan_name = serializers.CharField(source="membership_plan.name", read_only=True)
    status_text = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_text = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    display_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "user_phone",
            "user_nickname",
            "membership_plan",
            "plan_name",
            "amount",
            "display_amount",
            "status",
            "status_text",
            "payment_method",
            "payment_method_text",
            "paid_at",
            "created_at",
        ]

    def get_display_amount(self, obj) -> str:
        return f"¥{obj.amount:.2f}"


class OrderRefundResultSerializer(serializers.Serializer):
    """订单退款返回"""

    order_id = serializers.UUIDField()
    order_no = serializers.CharField()
    success = serializers.BooleanField()
    message = serializers.CharField()


# ============================================================
# Dashboard / 统计
# ============================================================

class DashboardSummarySerializer(serializers.Serializer):
    """核心指标卡片"""

    total_users = serializers.IntegerField()
    today_new_users = serializers.IntegerField()
    total_members = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_creations = serializers.IntegerField()
    today_creations = serializers.IntegerField()


class UserGrowthPointSerializer(serializers.Serializer):
    """近 30 天用户增长折线图点"""

    date = serializers.CharField()
    new_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


class MembershipPlanShareSerializer(serializers.Serializer):
    """会员套餐占比饼图"""

    plan_id = serializers.UUIDField()
    plan_name = serializers.CharField()
    member_count = serializers.IntegerField()
    percentage = serializers.FloatField()


class CreationDailySerializer(serializers.Serializer):
    """近 7 天创作柱状图"""

    date = serializers.CharField()
    count = serializers.IntegerField()


class DashboardDataSerializer(serializers.Serializer):
    """Dashboard 完整响应"""

    summary = DashboardSummarySerializer()
    user_growth_30d = UserGrowthPointSerializer(many=True)
    membership_share = MembershipPlanShareSerializer(many=True)
    creation_7d = CreationDailySerializer(many=True)


class StatsSummarySerializer(serializers.Serializer):
    """统计总览（更细粒度）"""

    users = DashboardSummarySerializer()
    orders = serializers.DictField()
    members = serializers.DictField()
    creations = serializers.DictField()
    cache_hit_rate = serializers.FloatField(required=False, default=0.0)


# ============================================================
# 系统设置
# ============================================================

class SystemSettingsSerializer(serializers.Serializer):
    """系统设置（只读快照，配置修改走具体模块）"""

    site_name = serializers.CharField()
    support_email = serializers.CharField()
    cache_backend = serializers.CharField()
    time_zone = serializers.CharField()
    debug_mode = serializers.BooleanField()
    api_rate_limit_per_hour = serializers.IntegerField()


class CacheClearResultSerializer(serializers.Serializer):
    """清除缓存结果"""

    success = serializers.BooleanField()
    message = serializers.CharField()
    cleared_keys = serializers.IntegerField()
