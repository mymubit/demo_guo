"""UGC 模板市场 AppConfig。"""
from django.apps import AppConfig


class UgcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.operations.ugc"
    label = "operations_ugc"
    verbose_name = "UGC 模板市场"
