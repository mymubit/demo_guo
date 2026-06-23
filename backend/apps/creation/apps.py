# -*- coding: utf-8 -*-
"""
创作模块 App 配置
"""

from django.apps import AppConfig


class CreationConfig(AppConfig):
    """创作模块 AppConfig"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.creation"
    verbose_name = "创作"
