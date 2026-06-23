# -*- coding: utf-8 -*-
"""Drama 产物展示层 — 基于 schema_version 契约，独立于旧 creation 工作台。"""

from apps.drama.presentation.service import build_execution_output_views, present_artifact

__all__ = ["build_execution_output_views", "present_artifact"]
