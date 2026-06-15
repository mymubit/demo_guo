"""
用户模块序列化器

包含注册、登录、资料查看与更新的序列化器
"""
import re

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import User, UserProfile


# ============================================================
# 公共工具
# ============================================================

PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


def validate_phone(value: str) -> str:
    """验证手机号格式（中国大陆手机号）"""
    if not value:
        raise serializers.ValidationError("手机号不能为空")
    if not PHONE_PATTERN.match(str(value).strip()):
        raise serializers.ValidationError("手机号格式不正确")
    return value


# ============================================================
# 注册
# ============================================================

class UserRegisterSerializer(serializers.Serializer):
    """用户注册序列化器

    字段：phone, password, password_confirm, nickname(可选)
    """
    phone = serializers.CharField(
        max_length=20,
        required=True,
        validators=[validate_phone],
        help_text="11位中国大陆手机号",
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=128,
        help_text="登录密码（8-128位）",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        help_text="与 password 完全一致",
    )
    nickname = serializers.CharField(
        max_length=64,
        required=False,
        allow_blank=True,
        help_text="可选的用户昵称",
    )

    def validate_password(self, value):
        """使用 Django 密码验证器校验强度"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages)) from e
        return value

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "两次输入的密码不一致"})

        # 检查手机号是否已注册
        from .models import _stable_hash
        phone_hash = _stable_hash(attrs["phone"], "ENCRYPT_PHONE_KEY")
        if User.objects.filter(phone_hash=phone_hash).exists():
            raise serializers.ValidationError({"phone": "该手机号已被注册"})
        return attrs

    def create(self, validated_data):
        """通过 User.objects.create_user 创建用户并返回 User 实例"""
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        phone = validated_data.pop("phone")
        nickname = validated_data.pop("nickname", "") or f"用户新{User.objects.count() + 1}"
        return User.objects.create_user(
            phone=phone,
            password=password,
            nickname=nickname,
        )


# ============================================================
# 登录
# ============================================================

class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器

    字段：phone, password
    """
    phone = serializers.CharField(
        max_length=20,
        required=True,
        validators=[validate_phone],
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        max_length=128,
    )

    def validate(self, attrs):
        phone = attrs.get("phone")
        password = attrs.get("password")
        if not phone or not password:
            raise serializers.ValidationError("手机号和密码均为必填")

        # 使用 Django authenticate（底层通过 get_by_natural_key 使用 phone_hash 查询）
        user = authenticate(request=self.context.get("request"), phone=phone, password=password)
        if user is None:
            raise serializers.ValidationError("手机号或密码错误")
        if not user.is_active:
            raise serializers.ValidationError("该账号已被禁用")

        attrs["user"] = user
        return attrs


# ============================================================
# 用户资料
# ============================================================

class UserProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器（GET）"""

    user_id = serializers.UUIDField(source="user.id", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    user_created_at = serializers.DateTimeField(source="user.created_at", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "phone",
            "email",
            "nickname",
            "avatar_url",
            "gender",
            "bio",
            "user_created_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码"""

    old_password = serializers.CharField(write_only=True, required=True, max_length=128)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8, max_length=128)
    new_password_confirm = serializers.CharField(write_only=True, required=True, max_length=128)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages)) from e
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "两次输入的密码不一致"})
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": "当前密码不正确"})
        return attrs


class UserUpdateSerializer(serializers.Serializer):
    """用户资料更新序列化器（PATCH）"""
    nickname = serializers.CharField(max_length=64, required=False, allow_blank=True)
    avatar_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=UserProfile.Gender.choices,
        required=False,
    )
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True)
    email = serializers.CharField(
        max_length=128,
        required=False,
        allow_blank=True,
        help_text="可选的新邮箱（将加密存储）",
    )

    def validate_email(self, value):
        if value:
            validator = EmailValidator(message="邮箱格式不正确")
            validator(value)
        return value

    def update(self, instance, validated_data):
        """instance 为 User 实例，同步更新 UserProfile"""
        profile_fields = ["nickname", "avatar_url", "gender", "bio"]
        user_fields = ["email"]

        # 更新 profile
        profile_data = {k: v for k, v in validated_data.items() if k in profile_fields}
        if profile_data:
            profile, _created = UserProfile.objects.update_or_create(
                user=instance,
                defaults=profile_data,
            )
            # 保证 nickname / avatar_url 同步回 User
            if "nickname" in profile_data and profile_data["nickname"]:
                instance.nickname = profile_data["nickname"]
            if "avatar_url" in profile_data and profile_data["avatar_url"]:
                instance.avatar_url = profile_data["avatar_url"]

        # 更新 user 自身字段
        if "email" in validated_data:
            instance.email = validated_data["email"]

        instance.save(update_fields=[f for f in ["nickname", "avatar_url", "email"] if hasattr(instance, f)])
        return instance
