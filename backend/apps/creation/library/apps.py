# -*- coding: utf-8 -*-
"""素材库应用配置。"""
from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.creation.library"
    verbose_name = "素材库"
