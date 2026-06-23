# -*- coding: utf-8 -*-
"""
用户模块的 AppConfig 配置
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """用户模块配置类

    定义 users 应用的基础配置，在 Django 启动时加载
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    verbose_name = "用户管理"
    label = "users"
