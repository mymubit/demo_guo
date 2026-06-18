"""
生产环境配置

继承 base.py，覆盖生产专用设置：
- DEBUG = False
- ALLOWED_HOSTS 从环境变量读取（逗号分隔）
- CORS 收紧为白名单
- 开启签名验证和限流
- 强制 HTTPS 安全头
"""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401, F403

DEBUG = False

_secret_key = os.getenv("SECRET_KEY", SECRET_KEY)
_insecure_markers = ("insecure", "change-me", "change_me", "django-insecure")
if not _secret_key or any(marker in _secret_key.lower() for marker in _insecure_markers):
    raise ImproperlyConfigured(
        "生产环境必须设置安全的 SECRET_KEY 环境变量，禁止使用默认值或占位符。"
    )
SECRET_KEY = _secret_key

# 生产环境开启请求签名验证（校验 API_SIGN_SECRET 前须先定义）
SECURITY_SIGNATURE_ENABLED = os.getenv("SECURITY_SIGNATURE_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)

_api_sign_secret = os.getenv("API_SIGN_SECRET", "")
if SECURITY_SIGNATURE_ENABLED and (
    not _api_sign_secret or "change" in _api_sign_secret.lower()
):
    raise ImproperlyConfigured(
        "生产环境开启签名验证时必须设置安全的 API_SIGN_SECRET。"
    )

# 逗号分隔的合法 Host 列表，示例：example.com,www.example.com
ALLOWED_HOSTS = [
    h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost").split(",") if h.strip()
]

# 生产环境关闭全量跨域，改用白名单
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
]

# 生产环境默认开启限流
SECURITY_RATE_LIMIT_ENABLED = os.getenv("SECURITY_RATE_LIMIT_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)

# 生产环境禁止模拟支付，防止零成本开通权益或充值到账。
ALLOW_MOCK_PAYMENT = False

# HTTPS 安全头
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "false").lower() in ("1", "true", "yes")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 生产环境关闭 LLM 全量轨迹，避免 prompt/剧本持久化
CREATION_LLM_TRACE_FULL = os.getenv("CREATION_LLM_TRACE_FULL", "false").lower() in ("1", "true", "yes")

_encrypt_keys = {
    "SKILL_ENCRYPT_KEY": os.getenv("SKILL_ENCRYPT_KEY", ""),
    "ENCRYPT_PHONE_KEY": os.getenv("ENCRYPT_PHONE_KEY", ""),
    "ENCRYPT_EMAIL_KEY": os.getenv("ENCRYPT_EMAIL_KEY", ""),
}
for _key_name, _key_val in _encrypt_keys.items():
    if not _key_val or "change" in _key_val.lower() or _key_val == "01234567890123456789012345678901":
        raise ImproperlyConfigured(
            f"生产环境必须设置安全的 {_key_name} 环境变量，禁止使用默认值或占位符。"
        )
SKILL_ENCRYPT_KEY = _encrypt_keys["SKILL_ENCRYPT_KEY"]
ENCRYPT_PHONE_KEY = _encrypt_keys["ENCRYPT_PHONE_KEY"]
ENCRYPT_EMAIL_KEY = _encrypt_keys["ENCRYPT_EMAIL_KEY"]
