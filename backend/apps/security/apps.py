"""
安全模块 AppConfig 配置
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SecurityConfig(AppConfig):
    """
    安全模块配置类

    负责模块初始化、信号注册、默认配置设置等。
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.security"
    label = "security"
    verbose_name = _("安全中心")
    icon = "🔒"

    def ready(self):
        """
        Django 应用就绪时执行。
        用于注册信号处理器、初始化资源等。
        """
        # 确保 services 模块被加载
        from . import services  # noqa: F401

        # 注册审计日志信号处理器（按需使用）
        # 目前通过 Middleware 实现审计记录，此处保留扩展点
