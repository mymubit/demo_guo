"""
用户模块业务逻辑服务层

将相对复杂的业务逻辑放在 services 中，由 views / serializers 调用，
保持视图层的简洁并便于后续单元测试。
"""
import logging
from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from .models import UserProfile

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================
# 用户查询
# ============================================================

def get_user_by_phone(phone: str) -> Optional[User]:
    """根据手机号查询用户（使用稳定哈希，不扫表解密）"""
    from .models import _stable_hash
    if not phone:
        return None
    phone_hash = _stable_hash(str(phone), "ENCRYPT_PHONE_KEY")
    return User.objects.filter(phone_hash=phone_hash).first()


def get_or_create_profile(user: User) -> UserProfile:
    """获取或创建用户资料"""
    profile, _created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "nickname": user.nickname or f"用户{user.id.hex[:8]}",
            "avatar_url": user.avatar_url or "",
        },
    )
    return profile


def is_phone_registered(phone: str) -> bool:
    """手机号是否已注册"""
    return get_user_by_phone(phone) is not None


# ============================================================
# 用户资料更新
# ============================================================

def update_user_profile(user: User, **fields) -> Tuple[User, UserProfile]:
    """更新用户资料（同时更新 User 和 UserProfile）

    :param user: 目标用户
    :param fields: 可更新字段：nickname, avatar_url, gender, bio, email
    :return: (user, profile)
    """
    profile_fields = {}
    user_fields = {}

    for key, value in fields.items():
        if key in ("nickname", "avatar_url", "gender", "bio"):
            if value is not None:
                profile_fields[key] = value
        elif key == "email" and value is not None:
            user_fields["email"] = value

    profile, _c = UserProfile.objects.update_or_create(
        user=user,
        defaults=profile_fields or {},
    )

    # 同步 User 的 nickname / avatar_url
    if "nickname" in profile_fields and profile_fields["nickname"]:
        user.nickname = profile_fields["nickname"]
    if "avatar_url" in profile_fields and profile_fields["avatar_url"]:
        user.avatar_url = profile_fields["avatar_url"]

    if user_fields:
        for k, v in user_fields.items():
            setattr(user, k, v)

    user.save(update_fields=["nickname", "avatar_url"] + list(user_fields.keys()))
    return user, profile
