# -*- coding: utf-8 -*-
"""编排引擎统一入口
========================================================
【P0】旧引擎全量下线 —— 本模块是创作流程的单一入口。

职责：
  ① 创建 WorkflowInstance（新引擎）
  ② 触发异步调度（Celery）
  ③ 统一进度查询
  ④ 外部控制（暂停/恢复/取消）

不再支持旧引擎（AgentOrchestrator / FusionOrchestrator），
所有创作请求必须走新引擎（WorkflowEngine）。

API：
  OrchestrationAdapter.run(project, user_id, pack_id=...)
    → {"instance_id": str, "status": str, ...}
  OrchestrationAdapter.get_progress(instance_id)
    → 统一结构（见 workflow_engine.get_instance_progress）
  OrchestrationAdapter.cancel(instance_id)
  OrchestrationAdapter.resume(instance_id, start_node_id=...)
========================================================
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from apps.workflow.execution_models import WorkflowInstance
from apps.workflow.workflow_engine import get_instance_progress
from apps.workflow.workflow_scheduler import WorkflowScheduler

if TYPE_CHECKING:
    from apps.creation.models import Project

logger = logging.getLogger(__name__)


class OrchestrationAdapter:
    """创作流程的单一调度入口。

    用法（views 中）:
        result = OrchestrationAdapter.run(
            project=project,
            user_id=str(request.user.id),
            pack_id=request.data.get("pack_id"),
        )
        return Response(result)
    """

    @staticmethod
    def run(
        *,
        project: "Project",
        user_id: str,
        pack_id: Optional[str] = None,
        start_node_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发起一次创作。

        Returns:
            {
              "instance_id": str,
              "status": "pending",
              "started_at": str | None,
              "progress": {"current_node_id": str, "progress_pct": int},
              "pack_version": str,
            }
        """
        instance = WorkflowScheduler.start_for_project(
            project=project,
            user_id=user_id,
            pack_id=pack_id,
            start_node_id=start_node_id,
        )

        return {
            "instance_id": str(instance.id),
            "status": instance.status,
            "started_at": (
                instance.started_at.isoformat()
                if instance.started_at else None
            ),
            "progress": {
                "current_node_id": instance.current_node_id or "",
                "progress_pct": 0,
            },
            "pack_version": instance.pack.version,
        }

    @staticmethod
    def get_progress(instance_id: str) -> Dict[str, Any]:
        """查询执行进度。"""
        try:
            instance = WorkflowInstance.objects.get(id=instance_id)
        except WorkflowInstance.DoesNotExist:
            return {
                "instance_id": instance_id,
                "status": "not_found",
                "progress_pct": 0,
            }

        return get_instance_progress(instance)

    @staticmethod
    def cancel(instance_id: str, *, reason: str = "user_cancel") -> Dict[str, Any]:
        WorkflowScheduler.cancel(instance_id, reason=reason)
        return {"instance_id": instance_id, "cancelled": True}

    @staticmethod
    def resume(instance_id: str, *, start_node_id: Optional[str] = None) -> Dict[str, Any]:
        WorkflowScheduler.resume(instance_id, start_node_id=start_node_id)
        return {"instance_id": instance_id, "resumed": True}


__all__ = ["OrchestrationAdapter"]
