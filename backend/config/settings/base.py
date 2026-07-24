# -*- coding: utf-8 -*-
"""Django 基础配置，所有环境共享。"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 优先读 backend/.env，其次读仓库根 .env（docker compose 共用）
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env", override=False)

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me-in-production")

DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "apps.core",
    "apps.users",
    "apps.drama",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "scriptforge"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {"connect_timeout": 30},
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=int(os.getenv("JWT_ACCESS_TTL", "3600"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(seconds=int(os.getenv("JWT_REFRESH_TTL", "86400"))),
    "ROTATE_REFRESH_TOKENS": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# Drama Skills 根目录（Git SSOT）：默认指向仓库内 drama-skills/
DRAMA_SKILLS_ROOT = os.getenv(
    "DRAMA_SKILLS_ROOT",
    str(BASE_DIR.parent / "drama-skills"),
)
# 注入策略预算护栏：false 时忽略 role.yaml 中 module/rule/knowledge 的 max_chars（逃生阀）
SKILLS_INJECTION_POLICY_ENFORCED = os.getenv(
    "SKILLS_INJECTION_POLICY_ENFORCED", "true"
).lower() in ("1", "true", "yes")
# 注入告警阈值（读详情时计算，不落库）
INJECTION_ALERT_SYSTEM_CHARS_ABS = int(
    os.getenv("INJECTION_ALERT_SYSTEM_CHARS_ABS", "100000")
)
INJECTION_ALERT_LAYER_DOMINANT_RATIO = float(
    os.getenv("INJECTION_ALERT_LAYER_DOMINANT_RATIO", "0.45")
)
# 可选：按角色覆盖绝对字数上限，形如 {"drama.story-bible": 80000}
INJECTION_ALERT_SYSTEM_CHARS_BY_ROLE: dict = {}

# LLM（OpenAI 兼容 HTTP）；本地开发默认关闭，避免误调外网
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() in ("1", "true", "yes")
LLM_CONNECT_TIMEOUT = int(os.getenv("LLM_CONNECT_TIMEOUT", "30"))
# 流式读超时=相邻数据包间隔；Celery 改超时后必须重启 worker
LLM_READ_TIMEOUT = int(os.getenv("LLM_READ_TIMEOUT", "900"))
# 单次补全 token 上限（防止模型管理里设过大导致极慢）
LLM_COMPLETION_MAX_TOKENS = int(os.getenv("LLM_COMPLETION_MAX_TOKENS", "8192"))
# 评分官长文输出（十维×约1000字 + 总评约2000字）需要更高补全上限
LLM_SCORER_MAX_TOKENS = int(os.getenv("LLM_SCORER_MAX_TOKENS", "24576"))
LLM_CALL_LOG_ENABLED = os.getenv("LLM_CALL_LOG_ENABLED", "true").lower() in ("1", "true", "yes")
# 三栏原文（system/user/response）完整落库；仅超过该硬顶才截断防炸库（默认 5MB）
LLM_CALL_LOG_MAX_TEXT_CHARS = int(os.getenv("LLM_CALL_LOG_MAX_TEXT_CHARS", "5000000"))
# 质检：默认串行（先评分达标再合规）；true 时评分与合规并行 chord
DRAMA_QUALITY_JUDGES_PARALLEL = os.getenv(
    "DRAMA_QUALITY_JUDGES_PARALLEL", "false"
).lower() in ("1", "true", "yes")

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"))
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() in (
    "1",
    "true",
    "yes",
)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_TRACK_STARTED = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# V3 测试注入点：可调用 (prompt) -> str；生产保持 None
V3_LLM_CALL_OVERRIDE = None

# 生成任务 SSE：必须 ≥ LLM 读超时，否则前端先断、后台还在跑
GENERATION_SSE_HEARTBEAT_SECONDS = int(os.getenv("GENERATION_SSE_HEARTBEAT_SECONDS", "15"))
GENERATION_SSE_MAX_WAIT_SECONDS = int(
    os.getenv("GENERATION_SSE_MAX_WAIT_SECONDS", str(LLM_READ_TIMEOUT + 180))
)
# 非终态超过此时长视为卡死（worker 崩溃等），查询时自动标记失败
GENERATION_JOB_STALE_SECONDS = int(
    os.getenv("GENERATION_JOB_STALE_SECONDS", str(LLM_READ_TIMEOUT + 600))
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
