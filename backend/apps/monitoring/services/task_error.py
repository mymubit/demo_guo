# -*- coding: utf-8 -*-
"""后台异步任务失败采集。

这类失败不经过 Django 请求中间件，必须在任务自身的统一收口处显式写入监控。
"""

from __future__ import annotations

from typing import Any

from apps.monitoring.services.sanitizer import stable_hash
from apps.monitoring.services.storage import store_backend_exception

TASK_FAILURE_STATUSES = {"failed", "exception", "error"}


def build_task_failure_extra(
    *,
    task_name: str,
    project_id: Any,
    node_index: int | None = None,
    status: str,
    detail: dict | None = None,
) -> dict[str, Any]:
    detail = detail if isinstance(detail, dict) else {}
    extra = {
        "task_name": task_name,
        "project_id": str(project_id),
        "status": status,
        "task_error": True,
        "detail": detail,
    }
    if node_index is not None:
        extra["node_index"] = node_index
    if detail.get("execution_run_id"):
        extra["execution_run_id"] = str(detail["execution_run_id"])
    return extra


def record_background_task_failure(
    *,
    task_name: str,
    project_id: Any,
    node_index: int | None = None,
    status: str,
    detail: dict | None = None,
    exception_type: str = "BackgroundTaskFailed",
) -> None:
    if status not in TASK_FAILURE_STATUSES:
        return

    detail = detail if isinstance(detail, dict) else {}
    message = str(detail.get("error") or detail.get("message") or "后台任务执行失败")
    path = f"task://{task_name}"
    if node_index is not None:
        path = f"{path}/node/{node_index}"

    store_backend_exception(
        exception_type=exception_type,
        message=message[:4000],
        stack="",
        path=path,
        method="TASK",
        status_code=None,
        fingerprint=stable_hash("task", task_name, project_id, node_index, message),
        extra=build_task_failure_extra(
            task_name=task_name,
            project_id=project_id,
            node_index=node_index,
            status=status,
            detail=detail,
        ),
    )


def record_agent_execution_failure(run: Any, *, error_message: str = "") -> None:
    message = str(error_message or getattr(run, "error_message", "") or "Agent 执行失败")
    project_id = getattr(run, "project_id", None)
    node_index = getattr(run, "node_index", None)
    agent_id = str(getattr(run, "agent_id", "") or "unknown")
    run_id = str(getattr(run, "id", "") or "")
    path = f"agent://{agent_id}"
    if node_index is not None:
        path = f"{path}/node/{node_index}"

    store_backend_exception(
        exception_type="AgentExecutionRunFailed",
        message=message[:4000],
        stack="",
        path=path,
        method="AGENT",
        status_code=None,
        user_id=getattr(run, "user_id", None),
        fingerprint=stable_hash("agent_run", run_id or project_id, agent_id, node_index, message),
        extra={
            "agent_error": True,
            "project_id": str(project_id or ""),
            "node_index": node_index,
            "agent_id": agent_id,
            "execution_run_id": run_id,
            "status": getattr(run, "status", ""),
            "input_summary": getattr(run, "input_summary", {}) or {},
        },
    )


def record_fusion_node_failure(
    *,
    project_id: Any,
    node_id: str,
    node_index: int | None = None,
    error: str,
    upstream: dict | None = None,
) -> None:
    path = f"fusion://{node_id or 'unknown'}"
    if node_index is not None:
        path = f"{path}/node/{node_index}"
    message = str(error or "融合节点执行失败")
    store_backend_exception(
        exception_type="FusionNodeFailed",
        message=message[:4000],
        stack="",
        path=path,
        method="FUSION",
        status_code=None,
        fingerprint=stable_hash("fusion_node", project_id, node_id, node_index, message),
        extra={
            "fusion_error": True,
            "project_id": str(project_id),
            "node_id": str(node_id or ""),
            "node_index": node_index,
            "upstream": upstream or {},
        },
    )
