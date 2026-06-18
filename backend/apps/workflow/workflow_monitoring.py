# -*- coding: utf-8 -*-
"""工作流监控指标（Legacy WorkflowInstance 已移除，基于 AgentExecutionRun）。"""
from __future__ import annotations

from datetime import timedelta
from typing import Dict

from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.creation.models import AgentExecutionRun
from apps.workflow.models import FusionPipelinePack


def collect_pipeline_metrics(*, last_n_minutes: int = 10, include_node_stats: bool = True) -> Dict[str, object]:
    now = timezone.now()
    cutoff = now - timedelta(minutes=last_n_minutes)
    runs_qs = AgentExecutionRun.objects.filter(started_at__gte=cutoff)

    by_status = list(
        runs_qs.values("status").annotate(count=Count("id")).order_by("status")
    )
    by_agent = list(
        runs_qs.values("agent_id", "status")
        .annotate(count=Count("id"))
        .order_by("-count")[:20]
    )
    durations = list(
        runs_qs.filter(
            status=AgentExecutionRun.STATUS_COMPLETED,
            started_at__isnull=False,
            finished_at__isnull=False,
        ).values_list("started_at", "finished_at")[:500]
    )
    duration_ms = [
        int((finished - started).total_seconds() * 1000)
        for started, finished in durations
        if started and finished
    ]
    duration_stats = {}
    if duration_ms:
        duration_stats = {
            "count": len(duration_ms),
            "avg_ms": int(sum(duration_ms) / len(duration_ms)),
            "max_ms": max(duration_ms),
        }

    return {
        "window_minutes": last_n_minutes,
        "agent_runs_by_status": by_status,
        "agent_runs_by_agent": by_agent,
        "duration_stats": duration_stats,
        "legacy_workflow_instances": {"removed": True},
    }


def export_prometheus_metrics(*, last_n_minutes: int = 10) -> str:
    metrics = collect_pipeline_metrics(last_n_minutes=last_n_minutes)
    lines = [
        "# HELP agent_execution_runs_total Agent runs in window",
        "# TYPE agent_execution_runs_total gauge",
    ]
    for row in metrics.get("agent_runs_by_status") or []:
        status = row.get("status") or "unknown"
        count = row.get("count") or 0
        lines.append(f'agent_execution_runs_total{{status="{status}"}} {count}')
    return "\n".join(lines) + "\n"


def pack_health_score(pack: FusionPipelinePack, *, last_n: int = 50) -> Dict[str, object]:
    runs = AgentExecutionRun.objects.order_by("-started_at")[: max(1, min(last_n, 200))]
    total = runs.count()
    if not total:
        return {
            "pack_id": str(pack.id),
            "pack_version": pack.version,
            "sample_count": 0,
            "success_rate": 0.0,
            "avg_duration_ms": 0,
        }
    completed = runs.filter(status=AgentExecutionRun.STATUS_COMPLETED).count()
    failed = runs.filter(status=AgentExecutionRun.STATUS_FAILED).count()
    avg_duration = runs.filter(
        started_at__isnull=False,
        finished_at__isnull=False,
    ).aggregate(avg=Avg("finished_at"))  # placeholder; compute below
    duration_samples = [
        int((run.finished_at - run.started_at).total_seconds() * 1000)
        for run in runs
        if run.started_at and run.finished_at
    ]
    avg_ms = int(sum(duration_samples) / len(duration_samples)) if duration_samples else 0
    _ = avg_duration
    return {
        "pack_id": str(pack.id),
        "pack_version": pack.version,
        "sample_count": total,
        "success_rate": round(completed / total, 4) if total else 0.0,
        "failure_rate": round(failed / total, 4) if total else 0.0,
        "avg_duration_ms": avg_ms,
        "note": "基于近期 AgentExecutionRun 抽样，非 WorkflowInstance",
    }
