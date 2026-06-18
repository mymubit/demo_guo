# -*- coding: utf-8 -*-
"""后台运营视角：项目状态统一展示（fusion_status SSOT，legacy status 仅内部过滤）。"""
from __future__ import annotations

from typing import Tuple

from .models import Project

LEGACY_TO_FUSION_STATUS = {
    Project.STATUS_PENDING: Project.FUSION_DRAFT,
    Project.STATUS_RUNNING: Project.FUSION_WRITING,
    Project.STATUS_AWAITING: Project.FUSION_REVIEWING,
    Project.STATUS_COMPLETED: Project.FUSION_READY,
    Project.STATUS_FAILED: Project.FUSION_BLOCKED,
}

_FUSION_LABELS = dict(Project.FUSION_STATUS_CHOICES)
_EXEC_LABELS = dict(Project.STATUS_CHOICES)


def resolve_admin_status(project: Project) -> Tuple[str, str]:
    """返回 (status, status_text) — 运营侧唯一状态字段。"""
    raw = (project.fusion_status or "").strip()
    if not raw:
        from .project_execution import derive_execution_status

        raw = LEGACY_TO_FUSION_STATUS.get(derive_execution_status(project), Project.FUSION_DRAFT)
    label = _FUSION_LABELS.get(raw) or _EXEC_LABELS.get(raw, raw)
    return raw, label
