# -*- coding: utf-8 -*-
"""双轨适配器：把新旧引擎统一暴露给创作接口
========================================================
设计目标：
  • 新的 views 层只需要知道 OrchestrationAdapter.run()
  • 内部根据灰度/参数决定走新引擎 WorkflowInstance
    还是旧引擎 AgentOrchestrator
  • 对外提供统一的"进度查询"接口（旧引擎通过
    step_mode + AgentExecutionRun 反推进度）

API：
  • OrchestrationAdapter.run(project, user_id, **opts)
    → {"instance_id": str, "use_new_engine": bool, ...}
  • OrchestrationAdapter.get_progress(instance_id)
    → 统一结构 (见 workflow_engine.get_instance_progress)
  • OrchestrationAdapter.cancel(instance_id)
========================================================
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.utils import timezone

from apps.workflow.execution_models import NodeExecution, WorkflowInstance
from apps.workflow.workflow_engine import get_instance_progress
from apps.workflow.workflow_scheduler import WorkflowScheduler


logger = logging.getLogger(__name__)


# =========================================================
# 适配器
# =========================================================
class OrchestrationAdapter:
    """创作流程的统一调度入口。

    典型用法（views 中）：
        adapter = OrchestrationAdapter()
        result = adapter.run(
            project=project,
            user_id=str(request.user.id),
            step_mode=None,
            pack_id=request.data.get("pack_id"),
            force_new_engine=request.data.get("force_new_engine"),
        )
        return Response(result)
    """

    @staticmethod
    def run(
        *,
        project: Any,
        user_id: str,
        step_mode: Optional[str] = None,
        pack_id: Optional[str] = None,
        start_node_id: Optional[str] = None,
        force_new_engine: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """启动创作。返回实例信息供前端轮询进度。"""
        instance = WorkflowScheduler.start_for_project(
            project=project,
            user_id=user_id,
            pack_id=pack_id,
            start_node_id=start_node_id,
            force_new_engine=force_new_engine,
        )

        # step_mode: 若前端需要立刻调用某个节点单独跑一遍，单独处理
        if step_mode and step_mode not in ("auto", "", None):
            logger.info("[Adapter] 以 step_mode=%s 启动（新引擎会忽略此参数）",
                        step_mode)

        return {
            "instance_id": str(instance.id),
            "use_new_engine": not bool((instance.context or {}).get("legacy_engine",
                                                                     False)),
            "status": instance.status,
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "progress": {
                "current_node_id": instance.current_node_id,
                "progress_pct": 0,
            },
        }

    @staticmethod
    def get_progress(instance_id: str) -> Dict[str, Any]:
        """查询执行进度。对新旧引擎返回一致的结构。"""
        try:
            instance = WorkflowInstance.objects.get(id=instance_id)
        except WorkflowInstance.DoesNotExist:
            return {"instance_id": instance_id, "status": "not_found", "progress_pct": 0}

        # 新引擎：直接读完整结构
        if not (instance.context or {}).get("legacy_engine", False):
            return get_instance_progress(instance)

        # 旧引擎：从 AgentExecutionRun 反推（P0 简化：直接返回 instance 状态）
        return _legacy_progress(instance)

    @staticmethod
    def cancel(instance_id: str, *, reason: str = "user_cancel") -> Dict[str, Any]:
        WorkflowScheduler.cancel(instance_id, reason=reason)
        return {"instance_id": instance_id, "cancelled": True}

    @staticmethod
    def resume(instance_id: str, *, start_node_id: Optional[str] = None) -> Dict[str, Any]:
        WorkflowScheduler.resume(instance_id, start_node_id=start_node_id)
        return {"instance_id": instance_id, "resumed": True}


# =========================================================
# 旧引擎进度（兼容层 —— 从现有数据反推）
# =========================================================
def _legacy_progress(instance: WorkflowInstance) -> Dict[str, Any]:
    """旧引擎（AgentOrchestrator）的进度：基于 project.status 做一个映射。"""
    try:
        from apps.creation.models import Project  # 避免循环依赖

        project = instance.project
        total_steps = len(getattr(project, "steps", []) or []) or 10
        current_step = int(getattr(project, "current_step_index", 0) or 0)
        pct = min(100, int((current_step / total_steps) * 100)) if total_steps else 0
    except Exception:
        pct = 0

    return {
        "instance_id": str(instance.id),
        "status": instance.status,
        "current_node_id": "",
        "progress_pct": pct,
        "total_nodes": 10,
        "done_nodes": int(pct / 10),
        "running_nodes": 1 if instance.status == "running" else 0,
        "failed_nodes": 0,
        "coin_used": 0,
        "llm_token_in": 0,
        "llm_token_out": 0,
        "elapsed_seconds": 0,
        "timeline": [],
        "legacy": True,
    }


__all__ = ["OrchestrationAdapter"]
