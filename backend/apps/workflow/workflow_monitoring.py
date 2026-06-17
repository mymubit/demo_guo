# -*- coding: utf-8 -*-
"""工作流监控指标与告警集成
========================================================
提供 Prometheus 风格的采集函数，以及业务关键指标的统计函数。
也可以直接对接项目已有的 monitoring 模块（若存在）。

核心指标：
  - workflow_instances_total{status, pack_version, trigger_type}
  - workflow_duration_seconds{pack_version, quantile}
  - node_execution_count{runner_type, status}
  - node_duration_seconds{runner_type, quantile}
  - node_retry_count{runner_type}
  - coin_cost_total{pack_version}
  - llm_token_total{pack_version, direction}
  - context_size_bytes{pack_version}

使用方式（views/management_command 中）：
    from apps.workflow.workflow_monitoring import collect_pipeline_metrics
    metrics = collect_pipeline_metrics(last_n_minutes=10)

或直接由 Prometheus 抓取：若项目已有一个 prometheus 导出器，
可以把 collect_pipeline_metrics 挂到 registry 上。
========================================================
"""
from __future__ import annotations

import logging
import statistics
from datetime import timedelta
from typing import Dict, List, Optional

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.workflow.execution_models import NodeExecution, WorkflowInstance
from apps.workflow.models import FusionPipelinePack


logger = logging.getLogger(__name__)


# =========================================================
# 指标：最近 N 分钟内实例级统计
# =========================================================
def collect_pipeline_metrics(
    *,
    last_n_minutes: int = 10,
    include_node_stats: bool = True,
) -> Dict[str, object]:
    """返回工作流层的结构化指标。

    本函数设计为轻量——仅在需要时按需聚合，不走缓存。
    若你的监控系统已有 pull/push 机制，建议每分钟调用一次。
    """
    now = timezone.now()
    cutoff = now - timedelta(minutes=last_n_minutes)

    # 实例级：按 status + pack_version 聚合
    instances_qs = WorkflowInstance.objects.filter(created_at__gte=cutoff)
    instances_total: Dict[str, int] = {}
    per_pack_stats: Dict[str, Dict[str, int]] = {}

    for stat in (
        instances_qs.values("status", "pack__version")
        .annotate(count=Count("id"))
    ):
        key = f"{stat['status']}|{stat['pack__version']}"
        instances_total[key] = stat["count"]
        per_pack_stats.setdefault(stat["pack__version"], {})[stat["status"]] = stat["count"]

    # 成功/失败的实例耗时统计（毫秒 → 秒）
    durations_ms = list(
        instances_qs.filter(
            Q(status="done") | Q(status="failed"),
            total_duration_ms__gt=0,
        ).values_list("total_duration_ms", flat=True)
    )
    if durations_ms:
        duration_stats = {
            "count": len(durations_ms),
            "avg_seconds": round(statistics.mean(durations_ms) / 1000.0, 3),
            "p50_seconds": round(statistics.median(durations_ms) / 1000.0, 3),
            "p95_seconds": round(_percentile(durations_ms, 95) / 1000.0, 3),
            "max_seconds": round(max(durations_ms) / 1000.0, 3),
        }
    else:
        duration_stats = {"count": 0}

    # 金币/Token 聚合
    coin_stats = (
        instances_qs.aggregate(
            total=Sum("coin_cost_total"),
            token_in=Sum("llm_token_in_total"),
            token_out=Sum("llm_token_out_total"),
        )
    )

    result: Dict[str, object] = {
        "window_minutes": last_n_minutes,
        "sampled_at": now.isoformat(),
        "instances_total": instances_total,
        "per_pack": per_pack_stats,
        "duration_seconds": duration_stats,
        "coin_cost": coin_stats["total"] or 0,
        "llm_tokens": {
            "in": coin_stats["token_in"] or 0,
            "out": coin_stats["token_out"] or 0,
        },
    }

    if include_node_stats:
        result["node_stats"] = collect_node_metrics(last_n_minutes=last_n_minutes)

    return result


# =========================================================
# 指标：节点级统计
# =========================================================
def collect_node_metrics(*, last_n_minutes: int = 10) -> Dict[str, object]:
    cutoff = timezone.now() - timedelta(minutes=last_n_minutes)
    qs = NodeExecution.objects.filter(created_at__gte=cutoff)

    by_status: Dict[str, int] = dict(
        qs.values_list("status").annotate(n=Count("id"))
    )
    by_runner: Dict[str, Dict[str, int]] = {}
    for stat in qs.values("runner_type", "status").annotate(n=Count("id")):
        by_runner.setdefault(stat["runner_type"] or "unknown", {})[stat["status"]] = stat["n"]

    # 重试次数：所有 attempt > 1 的节点占比
    retried = qs.filter(attempt__gt=1).count()
    total = qs.count() or 1
    retry_rate = round(retried * 100.0 / total, 2)

    # 节点成功率（按 runner_type 维度）
    success_by_runner: Dict[str, float] = {}
    for runner, stats in by_runner.items():
        total_runner = sum(stats.values())
        succeeded = stats.get("succeeded", 0)
        if total_runner > 0:
            success_by_runner[runner] = round(succeeded * 100.0 / total_runner, 2)

    # 平均重试次数
    avg_retry_count = qs.aggregate(avg=Sum("retry_count"))["avg"] or 0
    avg_retry_count = round(avg_retry_count / max(1, total), 3)

    # 配额回补统计
    refunded_total = qs.filter(quota_refunded=True).count()
    fallback_used_total = qs.filter(fallback_used=True).count()

    # 节点平均耗时（按 runner_type）
    durations = qs.values("runner_type").annotate(
        n=Count("id"),
        avg_ms=Sum("duration_ms"),
    )
    avg_duration_by_runner: Dict[str, Dict[str, float]] = {}
    for d in durations:
        runner = d["runner_type"] or "unknown"
        n = d["n"] or 1
        avg_ms = (d["avg_ms"] or 0) / n
        avg_duration_by_runner[runner] = {
            "n": d["n"] or 0,
            "avg_ms": round(avg_ms, 1),
        }

    return {
        "by_status": by_status,
        "by_runner_and_status": by_runner,
        "success_rate_pct_by_runner": success_by_runner,
        "avg_duration_ms_by_runner": avg_duration_by_runner,
        "retry_count_total": retried,
        "retry_rate_pct": retry_rate,
        "avg_retry_count_per_node": avg_retry_count,
        "quota_refunded_total": refunded_total,
        "fallback_used_total": fallback_used_total,
    }


# =========================================================
# Prometheus 文本格式导出（用于 /metrics 端点）
# =========================================================
def export_prometheus_metrics(*, last_n_minutes: int = 10) -> str:
    """返回 Prometheus exposition 格式的指标文本。

    用法（management command 或 HTTP 端点）：
        return HttpResponse(
            export_prometheus_metrics(),
            content_type="text/plain; version=0.0.4; charset=utf-8",
        )
    """
    metrics = collect_pipeline_metrics(last_n_minutes=last_n_minutes)
    node_stats = metrics.get("node_stats", {}) or {}

    lines: List[str] = []
    window = last_n_minutes

    # workflow_instances_total
    lines.append("# HELP workflow_instances_total Total workflow instances by status")
    lines.append("# TYPE workflow_instances_total counter")
    for key, count in (metrics.get("instances_total") or {}).items():
        status, pack_version = key.split("|", 1) if "|" in key else (key, "unknown")
        # Prometheus 标签值转义
        pv = pack_version.replace('"', '\\"')
        lines.append(
            f'workflow_instances_total{{status="{status}",pack_version="{pv}",window_minutes="{window}"}} {count}'
        )

    # workflow_duration_seconds
    duration_stats = metrics.get("duration_seconds") or {}
    if duration_stats.get("count", 0) > 0:
        lines.append("# HELP workflow_duration_seconds Workflow instance duration seconds")
        lines.append("# TYPE workflow_duration_seconds summary")
        for quantile, value in [
            ("avg", duration_stats.get("avg_seconds", 0)),
            ("p50", duration_stats.get("p50_seconds", 0)),
            ("p95", duration_stats.get("p95_seconds", 0)),
            ("max", duration_stats.get("max_seconds", 0)),
        ]:
            lines.append(f'workflow_duration_seconds{{quantile="{quantile}"}} {value}')

    # node_execution_total
    lines.append("# HELP node_execution_total Total node executions by status and runner")
    lines.append("# TYPE node_execution_total counter")
    for runner, stats in (node_stats.get("by_runner_and_status") or {}).items():
        runner_esc = runner.replace('"', '\\"')
        for status, n in stats.items():
            status_esc = status.replace('"', '\\"')
            lines.append(
                f'node_execution_total{{runner_type="{runner_esc}",status="{status_esc}",window_minutes="{window}"}} {n}'
            )

    # node_retry_count
    lines.append("# HELP node_retry_total Total node retries")
    lines.append("# TYPE node_retry_total counter")
    lines.append(f'node_retry_total{{window_minutes="{window}"}} {node_stats.get("retry_count_total", 0)}')

    # coin_cost_total
    lines.append("# HELP coin_cost_total Total coin cost in window")
    lines.append("# TYPE coin_cost_total counter")
    lines.append(f'coin_cost_total{{window_minutes="{window}"}} {metrics.get("coin_cost", 0)}')

    # llm_tokens_total
    lines.append("# HELP llm_tokens_total Total LLM tokens in window")
    lines.append("# TYPE llm_tokens_total counter")
    for direction, value in (metrics.get("llm_tokens") or {}).items():
        lines.append(f'llm_tokens_total{{direction="{direction}",window_minutes="{window}"}} {value}')

    return "\n".join(lines) + "\n"


# =========================================================
# 告警：当前活跃但超时的实例（>15 分钟未结束）
# =========================================================
def collect_stale_instances_alert(
    *,
    timeout_minutes: int = 15,
) -> List[Dict[str, str]]:
    """返回超时的"僵尸"实例列表（可直接接入告警频道）。

    例：
      alerts = collect_stale_instances_alert(timeout_minutes=15)
      if alerts:  send_alarm(channel="workflow-slack", message=alerts)
    """
    cutoff = timezone.now() - timedelta(minutes=timeout_minutes)
    stale = list(
        WorkflowInstance.objects.filter(
            status__in=["running", "waiting_human"],
            created_at__lte=cutoff,
        ).values(
            "id", "status", "pack__version", "current_node_id", "user_id",
            "created_at",
        )
    )
    return [
        {
            "instance_id": str(s["id"]),
            "status": s["status"],
            "pack_version": s["pack__version"],
            "current_node_id": s["current_node_id"],
            "user": s["user_id"],
            "running_since": s["created_at"].isoformat() if s["created_at"] else "",
            "alert_reason": f"已运行超过 {timeout_minutes} 分钟",
        }
        for s in stale
    ]


# =========================================================
# pack 健康度：最近 N 次执行的成功率/平均耗时
# =========================================================
def pack_health_score(
    pack: FusionPipelinePack,
    *,
    last_n: int = 50,
) -> Dict[str, object]:
    """为某个工作流包的版本计算健康度分数。

    用法（管理端 API 中调用）：
        pack = FusionPipelinePack.objects.get(version=v)
        health = pack_health_score(pack)
        # health = {"success_rate_pct": 98, "avg_duration_sec": 42, ...}
    """
    recent = list(
        WorkflowInstance.objects.filter(pack=pack).order_by("-created_at")[:last_n]
    )
    if not recent:
        return {"success_rate_pct": 0, "total_samples": 0, "avg_duration_sec": 0}

    success = sum(1 for r in recent if r.status == "done")
    finished = [r for r in recent if r.total_duration_ms > 0]
    avg_ms = (sum(r.total_duration_ms for r in finished) / len(finished)) if finished else 0
    return {
        "total_samples": len(recent),
        "success_rate_pct": round(success * 100.0 / len(recent), 2),
        "failed_count": sum(1 for r in recent if r.status == "failed"),
        "cancelled_count": sum(1 for r in recent if r.status == "cancelled"),
        "avg_duration_sec": round(avg_ms / 1000.0, 2),
        "sample_window_first": recent[-1].created_at.isoformat(),
        "sample_window_last": recent[0].created_at.isoformat(),
    }


# =========================================================
# 工具函数：百分位数（纯 Python 实现，避免 numpy 依赖）
# =========================================================
def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    pos = (len(sorted_values) - 1) * (pct / 100.0)
    lower = int(pos)
    upper = min(lower + 1, len(sorted_values) - 1)
    frac = pos - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * frac


__all__ = [
    "collect_pipeline_metrics",
    "collect_node_metrics",
    "collect_stale_instances_alert",
    "pack_health_score",
]
