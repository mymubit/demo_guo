# -*- coding: utf-8 -*-
"""后台 API 通用响应与缓存常量。"""
import secrets
import string

from rest_framework import status
from rest_framework.response import Response

from apps.orders.models import Order
from apps.users.models import User
from apps.skill.config.portal.skill_settings import SkillConfigService

# ============================================================
# 缓存 key 前缀与过期时间
# ============================================================
CACHE_KEY_DASHBOARD = "admin:dashboard:summary:v5"
CACHE_KEY_DASHBOARD_LEGACY = "admin:dashboard:summary"
CACHE_KEY_STATS = "admin:stats:summary"
CACHE_KEY_SKILL_CONFIG_PREFIX = "admin:skill:config:"
CACHE_TTL = 60 * 5  # 5 分钟


# 敏感 key 关键词（命中则列表返回时 value 显示为 ******）
_SENSITIVE_KEY_TOKENS = ("api_key", "secret", "password", "token")


def _is_sensitive_key(key: str) -> bool:
    k = (key or "").lower()
    return any(tok in k for tok in _SENSITIVE_KEY_TOKENS)


# 与 skill.services.SkillConfigService.DEFAULT_CONFIGS 保持一致
DEFAULT_CONFIG_KEYS = list(SkillConfigService.DEFAULT_CONFIGS.keys())


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


def api_ok(data=None, message: str = "success", code: int = 0,
        http_status: int = status.HTTP_200_OK, *, request=None, deprecated_path: str = ""):
    """统一响应包装；deprecated_path 非空且当前 path 不匹配时附加 api_meta.deprecated_paths。"""
    body = {"code": code, "message": message, "data": data}
    if request is not None and deprecated_path:
        current = (request.path or "").rstrip("/")
        target = deprecated_path.rstrip("/")
        if current and current != target:
            from apps.common.agent_term import attach_deprecated_paths

            body = attach_deprecated_paths(body, [deprecated_path])
    return Response(body, status=http_status)


def api_fail(message: str, code: int = 400, http_status: int = status.HTTP_200_OK,
          data=None):
    from apps.common.user_messages import humanize_user_message

    return Response(
        {
            "code": code,
            "message": humanize_user_message(message, default=message or "操作失败，请稍后重试"),
            "data": data,
        },
        status=http_status,
    )
