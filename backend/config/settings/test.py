# -*- coding: utf-8 -*-
"""测试环境配置。"""
from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("TEST_DB_NAME", os.getenv("DB_NAME", "scriptforge_test")),  # noqa: F405
        "USER": os.getenv("TEST_DB_USER", os.getenv("DB_USER", "postgres")),  # noqa: F405
        "PASSWORD": os.getenv("TEST_DB_PASSWORD", os.getenv("DB_PASSWORD", "postgres")),  # noqa: F405
        "HOST": os.getenv("TEST_DB_HOST", os.getenv("DB_HOST", "localhost")),  # noqa: F405
        "PORT": os.getenv("TEST_DB_PORT", os.getenv("DB_PORT", "5432")),  # noqa: F405
    }
}

CACHES = {  # noqa: F405
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("TEST_REDIS_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/15")),  # noqa: F405
    }
}

CELERY_TASK_ALWAYS_EAGER = os.getenv(  # noqa: F405
    "CELERY_TASK_ALWAYS_EAGER", "true"
).lower() in ("1", "true", "yes")
CELERY_TASK_EAGER_PROPAGATES = True  # noqa: F405
LLM_ENABLED = False  # noqa: F405
