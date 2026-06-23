# -*- coding: utf-8 -*-
"""??????????????creation.Project SSOT??"""
from __future__ import annotations

from typing import Tuple

from .models import Project


def resolve_admin_status(project: Project) -> Tuple[str, str]:
    """?? (status, status_text) ? ??????????"""
    from apps.drama.progress_service import DramaProgressService

    return DramaProgressService.resolve_admin_status(project)
