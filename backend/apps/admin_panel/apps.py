"""
admin_panel 应用配置
"""
from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    """后台管理面板应用配置
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_panel"
    verbose_name = "后台管理面板"
