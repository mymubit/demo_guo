"""按 DJANGO_ENV 选择环境配置。"""
import os

env = os.getenv("DJANGO_ENV", "development").lower()
if env == "production":
    from .production import *  # noqa: F401,F403
elif env == "test":
    from .test import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
