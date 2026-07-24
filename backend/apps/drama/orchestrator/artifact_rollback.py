# -*- coding: utf-8 -*-
"""V3 主链产物版本列表与回滚（R2）。"""
from __future__ import annotations

import copy

from django.db import transaction

from apps.drama.models import V3ArtifactVersion, V3Project
from apps.drama.orchestrator.artifacts import next_version

ALLOWED_ROLLBACK_KEYS = frozenset(
    {
        "project_brief",
        "story_bible",
        "character_system",
        "world_system",
        "emotion_system",
        "originality_report",
        "episode_plan",
        "episode_scripts",
    }
)

# 可回滚来源：当前 committed，以及曾确认后被替代的版本
_ROLLBACK_SOURCE_STATUSES = (
    V3ArtifactVersion.Status.COMMITTED,
    V3ArtifactVersion.Status.SUPERSEDED,
)


class ArtifactRollbackError(Exception):
    """回滚失败（人话消息）。"""


def _validate_key(artifact_key: str) -> str:
    key = (artifact_key or "").strip()
    if key not in ALLOWED_ROLLBACK_KEYS:
        raise ArtifactRollbackError(
            "不支持回滚该产物类型，请选择主链产物（选题/蓝图/分集/正文）"
        )
    return key


def list_committed_versions(
    project: V3Project, artifact_key: str
) -> list[V3ArtifactVersion]:
    """列出可回滚的历史版本（committed + superseded），按 version 降序。"""
    key = _validate_key(artifact_key)
    return list(
        V3ArtifactVersion.objects.filter(
            project=project,
            artifact_key=key,
            status__in=_ROLLBACK_SOURCE_STATUSES,
        ).order_by("-version")
    )


def rollback_artifact(
    *,
    project: V3Project,
    artifact_key: str,
    source_version: int,
    actor,
) -> V3ArtifactVersion:
    """将 source committed/superseded 的 payload 复制为新的 committed 版本。"""
    del actor  # 预留审计；当前无独立 actor 字段
    key = _validate_key(artifact_key)
    if not isinstance(source_version, int) or isinstance(source_version, bool):
        raise ArtifactRollbackError("source_version 必须为正整数")
    if source_version < 1:
        raise ArtifactRollbackError("source_version 必须为正整数")

    with transaction.atomic():
        try:
            source = V3ArtifactVersion.objects.select_for_update().get(
                project=project,
                artifact_key=key,
                version=source_version,
            )
        except V3ArtifactVersion.DoesNotExist as exc:
            raise ArtifactRollbackError("源版本不存在或不属于当前项目") from exc

        if source.status not in _ROLLBACK_SOURCE_STATUSES:
            raise ArtifactRollbackError("只能回滚已确认过的版本")

        new_version = next_version(project.id, key)
        created = V3ArtifactVersion.objects.create(
            project=project,
            artifact_key=key,
            version=new_version,
            schema_version=source.schema_version,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=copy.deepcopy(source.payload)
            if isinstance(source.payload, dict)
            else {},
            command_run=None,
        )
        V3ArtifactVersion.objects.filter(
            project=project,
            artifact_key=key,
            status__in=(
                V3ArtifactVersion.Status.COMMITTED,
                V3ArtifactVersion.Status.CANDIDATE,
            ),
        ).exclude(id=created.id).update(status=V3ArtifactVersion.Status.SUPERSEDED)
        return created
