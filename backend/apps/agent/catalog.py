# -*- coding: utf-8 -*-
"""
Agent Catalog — drama.* 新体系。

提供 C 端创作工作台所需的 Agent 目录数据。
按部门分组，包含快速通道标记。
旧的 brief/structure/character/outline 等已移除。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def portal_agent_catalog(
    track_mode: str = "fast",
    genre_code: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    获取创作工作台的 Agent 目录。

    参数：
    - track_mode: "fast"（标准创作通道）| "expert"（追加宣发交付）
    - genre_code: 可选，题材代码（future use）

    返回按部门分组的 Agent 列表。
    """
    try:
        from apps.agent.models import AgentDefinition
        from apps.agent.runtime import DRAMA_FAST_TRACK_AGENT_IDS

        agents = AgentDefinition.objects.filter(
            category="drama_skills",
            is_enabled=True,
            lifecycle_status=AgentDefinition.LifecycleStatus.ACTIVE,
        ).order_by("workspace_order")

        if track_mode == "fast":
            agents = agents.filter(agent_id__in=DRAMA_FAST_TRACK_AGENT_IDS)

        result = []
        for agent in agents:
            ui = agent.ui_schema or {}
            result.append({
                "id": agent.agent_id,
                "name": agent.name,
                "name_zh": agent.name_zh,
                "description": agent.description,
                "workspace_order": agent.workspace_order,
                "dept": ui.get("dept", ""),
                "is_fast_track": ui.get("is_fast_track", False),
                "can_run": True,
                "input_contract": agent.input_contract,
                "output_contract": agent.output_contract,
            })
        return result

    except Exception as exc:  # noqa: BLE001
        logger.warning("[portal_agent_catalog] failed: %s", exc)
        return []


def get_workspace_catalog(project_id: str, user_id: int) -> Dict[str, Any]:
    """
    获取指定项目的工作台 Agent 目录（含完成状态）。
    用于 C 端工作台页面渲染。
    """
    try:
        from apps.creation.models import Project
        from apps.drama.constants import DramaTrackMode

        project = Project.objects.filter(
            id=project_id,
            user_id=user_id,
            track_mode__in=[DramaTrackMode.FAST, DramaTrackMode.EXPERT],
        ).first()

        track_mode = project.track_mode if project else "fast"
        completed = set(project.completed_roles or []) if project else set()

        agents = portal_agent_catalog(track_mode=track_mode)

        for agent in agents:
            agent["is_completed"] = agent["id"] in completed

        return {
            "project_id": project_id,
            "track_mode": track_mode,
            "agents": agents,
            "total": len(agents),
            "completed_count": sum(1 for a in agents if a.get("is_completed")),
        }

    except Exception as exc:  # noqa: BLE001
        logger.warning("[get_workspace_catalog] project=%s failed: %s", project_id, exc)
        return {"project_id": project_id, "agents": []}
