# -*- coding: utf-8 -*-
"""开发环境配置。"""
from .base import *  # noqa: F401,F403

DEBUG = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")  # noqa: F405
