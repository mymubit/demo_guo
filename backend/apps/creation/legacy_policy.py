"""Legacy 流水线策略。"""
from django.conf import settings


def is_legacy_pipeline_enabled() -> bool:
    return bool(getattr(settings, "LEGACY_PIPELINE_ENABLED", False))
