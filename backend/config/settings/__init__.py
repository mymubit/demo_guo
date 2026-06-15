"""
Settings 入口：根据 DJANGO_ENV 环境变量自动选择 development 或 production 配置。

用法：
  DJANGO_ENV=development python manage.py runserver  （默认）
  DJANGO_ENV=production  gunicorn config.wsgi
"""
import os

_env = os.getenv("DJANGO_ENV", "development").lower().strip()

if _env == "production":
    from .production import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
