"""创作者激励 AppConfig。"""
from django.apps import AppConfig


class CreatorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.operations.creator"
    label = "operations_creator"
    verbose_name = "创作者激励"
