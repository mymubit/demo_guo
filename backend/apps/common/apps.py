# apps/common/apps.py
# 公共工具模块 AppConfig

from django.apps import AppConfig


class CommonConfig(AppConfig):
    """公共工具模块配置类。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.common'
    verbose_name = '公共工具'
