# -*- coding: utf-8 -*-
"""AI 规则进化引擎应用配置。"""
from django.apps import AppConfig


class EvolutionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.skill.evolution"
    verbose_name = "AI规则进化"
