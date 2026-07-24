# -*- coding: utf-8 -*-
"""GenerationJob API 序列化（前后端契约统一）。"""
from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
from typing import Any

from django.utils.dateparse import parse_datetime

from apps.drama.models import DramaGenerationJob


TERMINAL_STATUSES = frozenset(
    {
        DramaGenerationJob.Status.COMPLETED,
        DramaGenerationJob.Status.FAILED,
        DramaGenerationJob.Status.DISABLED,
    }
)

# 阶段基准进度（LLM 等待/流式阶段会再按耗时上浮）
_PHASE_PROGRESS: dict[str, int] = {
    "started": 8,
    "llm_started": 18,
    "llm_streaming": 35,
    "llm_done": 78,
    "artifact_saved": 90,
    "scoring_done": 94,
    "compliance_done": 97,
    "workflow_advanced": 99,
}


def resolve_external_review_title(payload: dict[str, Any] | None) -> str | None:
    """解析外部评测列表展示名：剧本名 > 文件名 > 正文首行。"""
    data = payload or {}
    for key in ("script_title", "title", "source_filename"):
        value = data.get(key)
        if isinstance(value, str):
            text = value.strip()
            if text:
                return text[:120]

    content = data.get("script_content")
    if not isinstance(content, str):
        return None
    for line in content.splitlines():
        text = line.strip().lstrip("#").strip()
        if text:
            return text[:80]
    return None


def _event_elapsed_seconds(event: dict[str, Any]) -> float:
    if isinstance(event.get("elapsed_ms"), (int, float)):
        return max(0.0, float(event["elapsed_ms"]) / 1000.0)
    raw_ts = event.get("ts")
    if not isinstance(raw_ts, str) or not raw_ts.strip():
        return 0.0
    parsed = parse_datetime(raw_ts)
    if parsed is None:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_timezone.utc)
    return max(0.0, (datetime.now(dt_timezone.utc) - parsed).total_seconds())


def compute_progress_from_events(
    events: list[dict[str, Any]] | None,
    *,
    status: str | None = None,
) -> int:
    """根据进度事件推算 0–100；运行中最高 99，避免假满格。"""
    if status == DramaGenerationJob.Status.COMPLETED:
        return 100
    if status in (
        DramaGenerationJob.Status.FAILED,
        DramaGenerationJob.Status.DISABLED,
    ):
        return 0

    items = [item for item in (events or []) if isinstance(item, dict)]
    if not items:
        if status in (
            DramaGenerationJob.Status.QUEUED,
            DramaGenerationJob.Status.PENDING,
            DramaGenerationJob.Status.RUNNING,
        ):
            return 3
        return 0

    best = 0
    for idx, event in enumerate(items):
        explicit = event.get("progress")
        if isinstance(explicit, (int, float)):
            best = max(best, int(explicit))
            continue

        phase = str(event.get("phase") or "")
        base = _PHASE_PROGRESS.get(phase)
        if base is None:
            best = max(best, min(90, (idx + 1) * 8))
            continue

        if phase == "llm_streaming":
            # 流式输出：18 → 75，约 2 分钟接近上限
            elapsed = _event_elapsed_seconds(event)
            best = max(best, min(75, 18 + int(elapsed / 2.0)))
        elif phase == "llm_started":
            # 等待首包：18 → 55，避免长时间停在固定值
            elapsed = _event_elapsed_seconds(event)
            best = max(best, min(55, 18 + int(elapsed / 4.0)))
        else:
            best = max(best, base)

    return min(99, max(0, best))


def serialize_generation_job(job: DramaGenerationJob) -> dict[str, Any]:
    """将 ORM 任务转为统一 GenerationJob 响应结构。"""
    events = job.progress_events or []
    last = events[-1] if events else {}
    progress = compute_progress_from_events(events, status=job.status)

    payload = job.request_payload if isinstance(job.request_payload, dict) else {}
    title = None
    source_filename = None
    if job.job_type in (
        DramaGenerationJob.JobType.EXTERNAL_REVIEW,
        DramaGenerationJob.JobType.PARALLEL_JUDGE,
    ):
        title = resolve_external_review_title(payload)
        raw_name = payload.get("source_filename")
        if isinstance(raw_name, str) and raw_name.strip():
            source_filename = raw_name.strip()[:120]

    return {
        "job_id": str(job.id),
        "project_id": str(job.project_id) if job.project_id else None,
        "job_type": job.job_type,
        "status": job.status,
        "role": job.role or payload.get("role"),
        "command_id": job.command_id or payload.get("command_id"),
        "artifact_key": job.artifact_key or None,
        "base_revision": job.base_revision,
        "operation_id": payload.get("operation_id"),
        "runtime_version": payload.get("runtime_version"),
        "v6_call": payload.get("v6_call"),
        "progress": progress,
        "message": last.get("message") or last.get("phase"),
        "error": job.error_message or None,
        "result": job.result_payload,
        "title": title,
        "source_filename": source_filename,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def sse_event_from_progress(
    job: DramaGenerationJob,
    raw: dict[str, Any],
    *,
    events_prefix: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """将内部进度事件规范为 SSE 载荷。"""
    event_type = raw.get("type")
    if not event_type:
        phase = raw.get("phase", "progress")
        if phase in (
            "started",
            "llm_started",
            "llm_streaming",
            "llm_done",
            "scoring_done",
            "compliance_done",
            "artifact_saved",
        ):
            event_type = "progress"
        else:
            event_type = "log"

    prefix = events_prefix if events_prefix is not None else (job.progress_events or [])
    progress = raw.get("progress")
    if not isinstance(progress, (int, float)):
        progress = compute_progress_from_events(prefix, status=job.status)

    message = raw.get("message") or raw.get("phase")
    phase = raw.get("phase")
    if phase == "llm_started" and not raw.get("message"):
        message = "正在调用模型…"
    elif phase == "llm_streaming":
        elapsed = raw.get("elapsed_ms")
        if isinstance(elapsed, (int, float)):
            message = f"模型生成中…（已 {int(elapsed / 1000)} 秒）"
        else:
            message = "模型生成中…"
    elif phase == "llm_done" and not raw.get("message"):
        message = "模型响应完成，正在解析…"
    elif phase == "artifact_saved" and not raw.get("message"):
        message = "产物已保存"

    return {
        "type": event_type,
        "job_id": str(job.id),
        "status": job.status,
        "progress": int(progress),
        "message": message,
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
        "progress": compute_progress_from_events(
            job.progress_events or [], status=job.status
        ),
        "done": True,
        "message": job.error_message or None,
    }


def sse_heartbeat_event(job: DramaGenerationJob) -> dict[str, Any]:
    """SSE 心跳，保持连接活跃，并附带当前推算进度。"""
    return {
        "type": "heartbeat",
        "job_id": str(job.id),
        "status": job.status,
        "progress": compute_progress_from_events(
            job.progress_events or [], status=job.status
        ),
        "done": False,
        "message": "任务仍在进行",
    }


def sse_timeout_event(job: DramaGenerationJob) -> dict[str, Any]:
    """SSE 等待超时。"""
    return {
        "type": "timeout",
        "job_id": str(job.id),
        "status": job.status,
        "progress": compute_progress_from_events(
            job.progress_events or [], status=job.status
        ),
        "done": True,
        "message": "等待任务进度超时",
    }
