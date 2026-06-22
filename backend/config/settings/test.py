"""测试环境配置 - 使用 SQLite 内存数据库，无需 PostgreSQL。"""
import os

from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

# 使用 SQLite 测试数据库，无需 PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/tmp/scriptforge_test.db",
        "TEST": {"NAME": "/tmp/scriptforge_test.db"},
    }
}

# 使用内存缓存代替 Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# 禁用任务队列
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# 使用 console 邮件后端
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# 覆盖需要外部服务的设置
REDIS_URL = "redis://127.0.0.1:6379/15"
CACHE_URL = "redis://127.0.0.1:6379/15"

# 禁用加密（测试无需真实密钥）
SKILL_ENCRYPT_KEY = "test-encrypt-key-32bytes-padding!"
ENCRYPT_PHONE_KEY = "test-phone-key"
ENCRYPT_EMAIL_KEY = "test-email-key"
API_SIGN_SECRET = "test-sign-secret-32bytes-min!!!!!"

# LLM 全局禁用（测试不调用真实 LLM）
FUSION_LLM_ENABLED = False
LLM_ENABLED = False
