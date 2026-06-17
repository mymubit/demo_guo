"""合规规则 AppConfig。"""
from django.apps import AppConfig


class ComplianceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.operations.compliance"
    label = "operations_compliance"
    verbose_name = "合规规则"
