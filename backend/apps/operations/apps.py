from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.operations"
    verbose_name = "运营中心"

    def ready(self):  # noqa: D401
        # 信号注册：实验曝光 / 任务激励 / 模板沉淀触发
        from . import signals  # noqa: F401
