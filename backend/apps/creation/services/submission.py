# -*- coding: utf-8 -*-
"""创作任务提交。

独立 Agent 架构下，本模块只负责创建 Project 与初始 project_brief 产物。
后续创作由用户在项目工作台手动触发单个 Agent。
"""

import logging
from typing import Tuple

from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.membership.services import MembershipService

from ..models import Project
from ._rendering import _render_progress_html

logger = logging.getLogger(__name__)


def _estimate_minutes(episode_count: int) -> int:
    base = 3
    per_episode = 0.3
    return max(1, int(base + episode_count * per_episode))


@transaction.atomic
def submit(user, data: dict) -> Tuple[Project, int]:
    """提交创作项目，不触发 workflow 或自动生成任务。"""
    from apps.billing.services import BillingService, InsufficientCoins

    BillingService.ensure_can_create(user)

    current_membership = MembershipService.get_current_membership(user)

    from apps.skill.config.portal.creation_catalog import get_creation_catalog as _get_catalog

    catalog = _get_catalog()
    platform = catalog.normalize_platform(data.get("target_platform", "douyin"))

    project = Project.objects.create(
        user=user,
        theme=data["theme"],
        core_idea=data["core_idea"],
        episode_count=data["episode_count"],
        format_variant=data["format_variant"],
        audience=data.get("audience", ""),
        reference_work=data.get("reference_work", ""),
        novel_text=(data.get("novel_text") or "").strip(),
        target_platform=platform,
        episode_duration_minutes=data.get("episode_duration_minutes", 2.0),
        creation_entry=data.get("creation_entry", "from-scratch"),
        budget_level=data.get("budget_level", "medium"),
        global_market=data.get("global_market", "domestic"),
        user_membership=current_membership,
        pipeline_mode=Project.MODE_WORKSPACE,
        progress_percent=0,
        title=catalog.theme_display_name(data["theme"]) or data["theme"],
        total_duration_minutes=0,
    )

    try:
        BillingService.charge(
            user,
            "creation.submit",
            reference_id=str(project.id),
            remark="发起创作",
        )
    except InsufficientCoins as exc:
        raise PermissionDenied(str(exc)) from exc

    try:
        from ..artifact_service import save_artifact
        from ..schema_mappers import build_project_brief

        brief_payload = build_project_brief(
            project, submit_data=data, status="confirmed",
        )
        save_artifact(project, "project_brief", brief_payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] 写入 project_brief 产物失败: %s", exc)

    project.rendered_progress_html = _render_progress_html(project)
    project.save(update_fields=["rendered_progress_html"])

    logger.info("[Creation] 独立 Agent 工作台项目已创建 project=%s user=%s", project.id, user.id)

    estimated_minutes = _estimate_minutes(project.episode_count)

    # 【运营 M6】埋点：创作提交（fire-and-forget；不影响主链路）
    try:
        from apps.operations.services import track_event
        track_event(
            event_name="creation_submitted",
            user=user,
            project_id=str(project.id),
            page="/api/creation/submit",
            payload={
                "theme": str(project.theme or "")[:120],
                "episode_count": project.episode_count,
                "pipeline_mode": project.pipeline_mode,
            },
            source="backend",
        )
    except Exception:  # noqa: BLE001
        pass

    return project, estimated_minutes
