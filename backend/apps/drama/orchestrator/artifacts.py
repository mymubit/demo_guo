# -*- coding: utf-8 -*-
"""V3 产物版本查询与分配 helper。"""
from __future__ import annotations

from uuid import UUID

from django.db.models import Max

from apps.drama.models import V3ArtifactVersion, V3Project


def next_version(project_id: UUID, artifact_key: str) -> int:
    """返回 project + artifact_key 的下一个版本号（从 1 起）。"""
    agg = V3ArtifactVersion.objects.filter(
        project_id=project_id,
        artifact_key=artifact_key,
    ).aggregate(max_version=Max("version"))
    current = agg["max_version"]
    return 1 if current is None else current + 1


def latest(
    project: V3Project,
    artifact_key: str,
    status: str | None = None,
) -> V3ArtifactVersion | None:
    """返回指定 project + artifact_key 的最高 version 行；可按 status 过滤。"""
    qs = V3ArtifactVersion.objects.filter(project=project, artifact_key=artifact_key)
    if status is not None:
        qs = qs.filter(status=status)
    return qs.order_by("-version").first()
