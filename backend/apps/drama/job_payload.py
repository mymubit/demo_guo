# -*- coding: utf-8 -*-
"""GenerationJob API 序列化（前后端契约统一）。"""
from __future__ import annotations

from typing import Any

from apps.drama.models import DramaGenerationJob


TERMINAL_STATUSES = frozenset(
    {
        DramaGenerationJob.Status.COMPLETED,
        DramaGenerationJob.Status.FAILED,
        DramaGenerationJob.Status.DISABLED,
    }
)


def serialize_generation_job(job: DramaGenerationJob) -> dict[str, Any]:
    """将 ORM 任务转为统一 GenerationJob 响应结构。"""
    events = job.progress_events or []
    last = events[-1] if events else {}
    progress = last.get("progress")
    if progress is None and events:
        progress = min(100, len(events) * 10)

    return {
        "job_id": str(job.id),
        "project_id": str(job.project_id) if job.project_id else None,
        "job_type": job.job_type,
        "status": job.status,
        "role": job.role or job.request_payload.get("role"),
        "command_id": job.command_id or job.request_payload.get("command_id"),
        "artifact_key": job.artifact_key or None,
        "workflow_version": job.workflow_version,
        "progress": progress if progress is not None else 0,
        "message": last.get("message") or last.get("phase"),
        "error": job.error_message or None,
        "result": job.result_payload,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def sse_event_from_progress(
    job: DramaGenerationJob, raw: dict[str, Any]
) -> dict[str, Any]:
    """将内部进度事件规范为 SSE 载荷。"""
    event_type = raw.get("type")
    if not event_type:
        phase = raw.get("phase", "progress")
        if phase in ("started", "llm_done", "scoring_done", "compliance_done"):
            event_type = "progress"
        else:
            event_type = "log"
    return {
        "type": event_type,
        "job_id": str(job.id),
        "status": job.status,
        "progress": raw.get("progress"),
        "message": raw.get("message") or raw.get("phase"),
        "data": raw.get("data"),
    }


def sse_terminal_event(job: DramaGenerationJob) -> dict[str, Any]:
    """任务结束时的 SSE 事件。"""
    if job.status == DramaGenerationJob.Status.FAILED:
        event_type = "error"
    elif job.status == DramaGenerationJob.Status.DISABLED:
        event_type = "done"
    else:
        event_type = "done"
    return {
        "type": event_type,
        "job_id": str(job.id),
        "status": job.status,
        "done": True,
        "message": job.error_message or None,
    }


def sse_heartbeat_event(job: DramaGenerationJob) -> dict[str, Any]:
    """SSE 心跳，保持连接活跃。"""
    return {
        "type": "heartbeat",
        "job_id": str(job.id),
        "status": job.status,
        "done": False,
    }


def sse_timeout_event(job: DramaGenerationJob) -> dict[str, Any]:
    """SSE 等待超时。"""
    return {
        "type": "timeout",
        "job_id": str(job.id),
        "status": job.status,
        "done": True,
        "message": "等待任务进度超时",
    }
