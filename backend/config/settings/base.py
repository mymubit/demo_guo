"""
Django settings for ScriptForge project.

基础配置 - 所有环境共享的基础设置
"""
import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me-in-production")

DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "dj_queue",
    # Project apps
    "apps.users",
    "apps.membership",
    "apps.billing",
    "apps.orders",
    "apps.creation",
    "apps.skill",
    "apps.agent",
    "apps.workflow",
    "apps.security",
    "apps.monitoring",
    "apps.system_config",
    "apps.portal",
    "apps.console",
    "apps.operations",
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
    # Custom security middleware
    "apps.security.middleware.RequestSignatureMiddleware",
    "apps.security.middleware.RateLimitMiddleware",
    "apps.security.middleware.AuditLogMiddleware",
    "apps.monitoring.middleware.MonitoringRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATE_DIR = BASE_DIR / "templates"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATE_DIR] if TEMPLATE_DIR.exists() else [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "scriptforge"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {
            "connect_timeout": 30,
        },
    }
}
#python manage.py dj_queue --mode async

# Cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("CACHE_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# Django 6 Tasks + dj_queue（Postgres 队列，无需 Celery/Redis broker）
DATABASE_ROUTERS = ["dj_queue.routers.DjQueueRouter"]


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


DJ_QUEUE_QUEUES = _csv_env("DJ_QUEUE_QUEUES", "creation,default,evolve")

TASKS = {
    "default": {
        "BACKEND": "dj_queue.backend.DjQueueBackend",
        "QUEUES": DJ_QUEUE_QUEUES,
        "OPTIONS": {
            # Windows 本地开发用 async；Linux 生产可设 DJ_QUEUE_MODE=fork
            "mode": os.getenv("DJ_QUEUE_MODE", "async"),
            "workers": [
                {
                    "queues": DJ_QUEUE_QUEUES,
                    "threads": int(os.getenv("DJ_QUEUE_WORKER_THREADS", "2")),
                    "processes": 1,
                    "polling_interval": 0.2,
                }
            ],
            # Windows 上 psycopg2 的 LISTEN/NOTIFY 不可用，改轮询
            "listen_notify": (
                os.getenv("DJ_QUEUE_LISTEN_NOTIFY", "false" if sys.platform == "win32" else "true").lower()
                in ("1", "true", "yes")
            ),
        },
    },
}

# 仅调试：True 时提交接口同步跑完整流水线（会阻塞 HTTP）
CREATION_FORCE_SYNC_PIPELINE = os.getenv(
    "CREATION_FORCE_SYNC_PIPELINE", "false"
).lower() in ("1", "true", "yes")

# 模拟支付仅允许开发/测试显式开启，生产环境必须关闭。
ALLOW_MOCK_PAYMENT = os.getenv("ALLOW_MOCK_PAYMENT", "false").lower() in (
    "1",
    "true",
    "yes",
)


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Custom user model
AUTH_USER_MODEL = "users.User"


# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "1000/hour",
        "anon": "100/hour",
        "monitoring_anon": os.getenv("MONITORING_ANON_RATE", "300/min"),
        "monitoring_user": os.getenv("MONITORING_USER_RATE", "600/min"),
    },
}


# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=int(os.getenv("JWT_ACCESS_TTL", 3600))),
    "REFRESH_TOKEN_LIFETIME": timedelta(seconds=int(os.getenv("JWT_REFRESH_TTL", 86400))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": "rest_framework_simplejwt.token_blacklist" in INSTALLED_APPS,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": "ScriptForge",
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}


# CORS - 基础公共配置，CORS_ALLOW_ALL_ORIGINS 由 development.py/production.py 覆盖
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https?://localhost:\d+$",
    r"^https?://127\.0\.0\.1:\d+$",
]


# Internationalization
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_DIR = BASE_DIR / "static"
STATICFILES_DIRS = [STATIC_DIR] if STATIC_DIR.exists() else []

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Security settings - 安全开关由各环境配置文件覆盖（development.py / production.py）
SKILL_ENCRYPT_KEY = os.getenv("SKILL_ENCRYPT_KEY", "01234567890123456789012345678901")

# External skill folders are one-time migration sources only. Runtime is DB-only.
SCRIPT_FORGE_ASSET_ROOT = os.getenv(
    "SCRIPT_FORGE_ASSET_ROOT",
    str(BASE_DIR / "apps" / "skill" / "assets"),
)
FUSION_SKILL_ENABLED = False
CREATION_FUSION_WORK_DIR = os.getenv(
    "CREATION_FUSION_WORK_DIR",
    str(BASE_DIR / "tmp" / "fusion_work"),
)
# Legacy 流水线已下线；FUSION_ORCHESTRATOR_ENABLED 固定关闭
FUSION_ORCHESTRATOR_ENABLED = False
FUSION_LLM_ENABLED = os.getenv("FUSION_LLM_ENABLED", "true").lower() in ("1", "true", "yes")
FUSION_LLM_EPISODE_BATCH = int(os.getenv("FUSION_LLM_EPISODE_BATCH", "5"))
FUSION_LLM_OUTLINE_BATCH = int(os.getenv("FUSION_LLM_OUTLINE_BATCH", "1"))
FUSION_LLM_MAX_EPISODES = int(os.getenv("FUSION_LLM_MAX_EPISODES", "0"))  # 0=全部集数
FUSION_LLM_MAX_TOKENS = int(os.getenv("FUSION_LLM_MAX_TOKENS", "6000"))
# CREATION_LLM_TRACE_FULL 默认关闭；生产环境务必保持 false，避免 prompt/剧本落库
CREATION_LLM_TRACE_FULL = os.getenv("CREATION_LLM_TRACE_FULL", "false").lower() in ("1", "true", "yes")
CREATION_LLM_TRACE_MAX_CHARS = int(os.getenv("CREATION_LLM_TRACE_MAX_CHARS", "262144"))
# upstream 轨迹：summary=仅键名/规模摘要 | off=不存 | full=全量（调试用，体积大）
CREATION_LLM_TRACE_UPSTREAM_MODE = os.getenv("CREATION_LLM_TRACE_UPSTREAM_MODE", "summary").lower()
# Prompt 中 upstream_json 按 sub_skill 裁剪 + 去重 snake/camel 别名
CREATION_LLM_UPSTREAM_SLIM_PROMPT = os.getenv("CREATION_LLM_UPSTREAM_SLIM_PROMPT", "true").lower() in ("1", "true", "yes")
FUSION_SCHEMA_STRICT = os.getenv("FUSION_SCHEMA_STRICT", "false").lower() in (
    "1",
    "true",
    "yes",
)
FUSION_EPISODE_GATE_ENABLED = os.getenv(
    "FUSION_EPISODE_GATE_ENABLED", "true"
).lower() in ("1", "true", "yes")
# Phase C：主链 + Schema 运行时只读 DB；磁盘仅用于 import/sync 引导
FUSION_DB_CONFIG = os.getenv("FUSION_DB_CONFIG", "true").lower() in ("1", "true", "yes")
FUSION_CONFIG_DISK_FALLBACK = os.getenv("FUSION_CONFIG_DISK_FALLBACK", "false").lower() in (
    "1",
    "true",
    "yes",
)
ENCRYPT_PHONE_KEY = os.getenv("ENCRYPT_PHONE_KEY", "phone-encrypt-key-change-me")
ENCRYPT_EMAIL_KEY = os.getenv("ENCRYPT_EMAIL_KEY", "email-encrypt-key-change-me")

# LLM（init_skill_data 会灌入 SkillConfig 数据库；endpoint 可为完整 /chat/completions URL）
LLM_API_ENDPOINT = os.getenv("LLM_API_ENDPOINT", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_CONNECT_TIMEOUT = int(os.getenv("LLM_CONNECT_TIMEOUT", "30"))
LLM_READ_TIMEOUT_JSON = int(os.getenv("LLM_READ_TIMEOUT_JSON", "600"))
LLM_READ_TIMEOUT_TEXT = int(os.getenv("LLM_READ_TIMEOUT_TEXT", "120"))
LLM_REQUEST_RETRIES = int(os.getenv("LLM_REQUEST_RETRIES", "2"))

# 火山方舟统一接入（setup_volcano_agent_llm 管理命令读取）
VOLCANO_ARK_API_KEY = os.getenv("VOLCANO_ARK_API_KEY", "")
VOLCANO_ARK_BASE_URL = os.getenv(
    "VOLCANO_ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
)
# Coding Plan / Agent Plan 专用（OpenAI 兼容）
VOLCANO_ARK_CODING_BASE_URL = os.getenv(
    "VOLCANO_ARK_CODING_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding/v3"
)
# coding_plan | payg — setup / env-setup 创建火山 Provider 时使用
VOLCANO_ARK_KEY_TYPE = os.getenv("VOLCANO_ARK_KEY_TYPE", "")
VOLCANO_EP_DEEPSEEK_V4_FLASH = os.getenv("VOLCANO_EP_DEEPSEEK_V4_FLASH", "")
VOLCANO_EP_DEEPSEEK_V4_PRO = os.getenv("VOLCANO_EP_DEEPSEEK_V4_PRO", "")
VOLCANO_EP_DOUBAO_LITE = os.getenv("VOLCANO_EP_DOUBAO_LITE", "")
VOLCANO_EP_DOUBAO_PRO = os.getenv("VOLCANO_EP_DOUBAO_PRO", "")
VOLCANO_EP_MINIMAX_M27 = os.getenv("VOLCANO_EP_MINIMAX_M27", "")
# 按量付费 Chat API：model 填 ep-xxx；若 DB 存 Model ID，可通过以上 VOLCANO_EP_* 自动映射到接入点

# 智谱 GLM-5 原生 API（Script 节点；不走火山 ep-xxx）
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_GLM5_MODEL = os.getenv("ZHIPU_GLM5_MODEL", "glm-5")
ZHIPU_GLM5_TURBO_MODEL = os.getenv("ZHIPU_GLM5_TURBO_MODEL", "glm-5-turbo")


# Security - 安全中间件基础配置
# 直接加载 base.py 时也需要安全默认值；development/production 会按环境覆盖。
SECURITY_SIGNATURE_ENABLED = os.getenv("SECURITY_SIGNATURE_ENABLED", "false").lower() in (
    "1",
    "true",
    "yes",
)
SECURITY_RATE_LIMIT_ENABLED = os.getenv("SECURITY_RATE_LIMIT_ENABLED", "false").lower() in (
    "1",
    "true",
    "yes",
)
SECURITY_SIGNATURE_SKIP_PATHS = ("/api/auth/", "/api/monitoring/", "/health", "/api/health/")

# 限流：默认每 IP+用户每分钟 120 次；匿名用户按 DRF throttle 配置
SECURITY_RATE_LIMIT_DEFAULT = int(os.getenv("SECURITY_RATE_LIMIT_DEFAULT", "120") or 120)
SECURITY_RATE_LIMIT_SKIP_PATHS = (
    "/api/auth/",
    "/api/health/",
    "/api/admin/",
    "/api/monitoring/",
    # 只读 SSOT 目录（创作页首屏单次加载，不应计入创作接口限频）
    "/api/creation/fusion/catalog/",
    "/api/creation/agents/catalog/",
    "/api/creation/fusion/nodes/",
    "/api/skill/themes/",
)

# 审计日志：默认开启；如 Redis 不可用可关闭
SECURITY_AUDIT_ENABLED = True
SECURITY_AUDIT_SKIP_PATHS = ("/api/health/", "/api/monitoring/")

# 签名密钥（与前端共享）
# 注意：生产环境必须修改为安全随机值
API_SIGN_SECRET = os.getenv("API_SIGN_SECRET", "scriptforge-demo-sign-secret-change-me")
# 签名时间窗口（秒）
SIGNATURE_TIME_WINDOW = 300  # 5 分钟


# Monitoring - 项目内自研业务监控
MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "true").lower() in ("1", "true", "yes")
MONITORING_SAMPLE_RATE = float(os.getenv("MONITORING_SAMPLE_RATE", "1") or 1)
MONITORING_SLOW_API_MS = int(os.getenv("MONITORING_SLOW_API_MS", "1000") or 1000)
MONITORING_SLOW_SQL_MS = int(os.getenv("MONITORING_SLOW_SQL_MS", "500") or 500)
MONITORING_RETENTION_DAYS = int(os.getenv("MONITORING_RETENTION_DAYS", "30") or 30)
MONITORING_MAX_BATCH_SIZE = int(os.getenv("MONITORING_MAX_BATCH_SIZE", "50") or 50)
MONITORING_MAX_PAYLOAD_SIZE = int(os.getenv("MONITORING_MAX_PAYLOAD_SIZE", str(16 * 1024)) or 16 * 1024)
MONITORING_CAPTURE_RESPONSE = os.getenv("MONITORING_CAPTURE_RESPONSE", "false").lower() in (
    "1",
    "true",
    "yes",
)
MONITORING_SKIP_PATHS = (
    "/api/health/",
    "/api/monitoring/",
    "/static/",
    "/media/",
)
MONITORING_BUSINESS_ERROR_LOG_ENABLED = os.getenv(
    "MONITORING_BUSINESS_ERROR_LOG_ENABLED", "true"
).lower() in ("1", "true", "yes")
MONITORING_BUSINESS_ERROR_SAMPLE_RATE = float(
    os.getenv("MONITORING_BUSINESS_ERROR_SAMPLE_RATE", "1") or 1
)
MONITORING_VALIDATION_ERROR_SAMPLE_RATE = float(
    os.getenv("MONITORING_VALIDATION_ERROR_SAMPLE_RATE", "0.1") or 0.1
)


# 文件存储
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "scriptforge")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")


# 日志
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "app.log",
            "maxBytes": 1024 * 1024 * 10,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.skill": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps.creation": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.monitoring": {
            "handlers": ["console", "file"],
            "level": os.getenv("MONITORING_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "apps.monitoring.business": {
            "handlers": ["console", "file"],
            "level": os.getenv("MONITORING_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# OpenAPI（drf-spectacular）
SPECTACULAR_SETTINGS = {
    "TITLE": "ScriptForge API",
    "DESCRIPTION": "ScriptForge 前台 / 后台 REST API 契约",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "DISABLE_ERRORS_AND_WARNINGS": True,
}
