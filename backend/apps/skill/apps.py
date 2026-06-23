# -*- coding: utf-8 -*-
"""
apps/skill - AppConfig
"""
from django.apps import AppConfig


class SkillConfig(AppConfig):
    """技能引擎配置与后台管理模块"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.skill'
    verbose_name = '技能引擎'

    def ready(self):
        """Django 应用加载完成后执行"""
        # 可在此注册信号或懒加载初始化逻辑
        pass
