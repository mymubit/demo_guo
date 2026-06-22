# -*- coding: utf-8 -*-
"""后台运营视角：项目状态展示（DramaProject SSOT）。"""
from __future__ import annotations

from typing import Tuple

from .models import Project


def resolve_admin_status(project: Project) -> Tuple[str, str]:
    """返回 (status, status_text) — 运营侧唯一状态字段。"""
    from apps.drama.progress_service import DramaProjectProgressService

    return DramaProjectProgressService.resolve_admin_status(project)
