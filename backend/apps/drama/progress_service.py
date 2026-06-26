# -*- coding: utf-8 -*-
"""Drama 项目进度 / 阶段 / 交付 状态管理，作为 creation.Project 的 SSOT"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from django.db.models import Q

from apps.creation.models import Project
from apps.drama.constants import DramaStage, DramaTrackMode
from apps.drama.models import DramaRoleExecution
from apps.drama.skills_registry import DELIVERY_AGENT_IDS, QUALITY_AGENT_ID, build_agent_phase_map

logger = logging.getLogger(__name__)


class DramaProgressService:
    """Drama 项目进度计算与状态同步，写入 creation.Project 字段"""

    @staticmethod
    def workspace_projects_qs():
        return Project.objects.filter(
            track_mode__in=[DramaTrackMode.FAST, DramaTrackMode.EXPERT]
        )

    @classmethod
    def list_track_agent_ids(cls, project: Project) -> List[str]:
        from apps.creation.agent_runtime.entry_plan import DramaEntryPlan

        plan = DramaEntryPlan.resolve(
            track_mode=project.track_mode,
            entry_type="from-scratch",
        )
        if plan.get("recommended_agents"):
            return list(plan["recommended_agents"])
        agents: List[str] = []
        for phase in plan.get("phases") or []:
            agents.extend(phase.get("agents") or [])
        return agents

    @classmethod
    def agent_phase_map(cls, project: Project) -> Dict[str, str]:
        track_mode = project.track_mode or DramaTrackMode.FAST
        return build_agent_phase_map(track_mode)

    @classmethod
    def resolve_current_stage(cls, project: Project) -> str:
        completed = set(project.completed_roles or [])
        track_agents = cls.list_track_agent_ids(project)
        phase_map = cls.agent_phase_map(project)

        if not track_agents:
            return project.drama_stage or DramaStage.STRATEGY

        if all(agent_id in completed for agent_id in track_agents):
            if any(a in completed for a in DELIVERY_AGENT_IDS):
                return DramaStage.DELIVERED
            return DramaStage.COMPLIANCE

        for agent_id in track_agents:
            if agent_id not in completed:
                return phase_map.get(agent_id, DramaStage.STRATEGY)

        return project.drama_stage or DramaStage.STRATEGY

    @classmethod
    def resolve_delivery_status(cls, project: Project) -> str:
        completed = set(project.completed_roles or [])
        if "drama.production-pack" in completed:
            return "delivered"
        if DELIVERY_AGENT_IDS & completed:
            return "ready"
        return project.delivery_status or "pending"

    @classmethod
    def extract_quality_scores(cls, project: Project) -> Dict[str, Any]:
        exec_row = (
            DramaRoleExecution.objects.filter(
                project=project,
                agent_id=QUALITY_AGENT_ID,
                status=DramaRoleExecution.Status.SUCCESS,
            )
            .order_by("-finished_at")
            .first()
        )
        if not exec_row:
            return dict(project.quality_scores or {})

        outputs = exec_row.output_artifacts or {}
        for key in ("quality_report", "score_report", "quality_scores"):
            payload = outputs.get(key)
            if isinstance(payload, dict):
                scores = payload.get("scores") or payload.get("dimensions") or payload
                if isinstance(scores, dict) and scores:
                    merged = dict(project.quality_scores or {})
                    merged.update(scores)
                    if "overall" in payload:
                        merged["overall"] = payload["overall"]
                    return merged
        return dict(project.quality_scores or {})

    @classmethod
    def recompute_project_state(cls, project: Project) -> Project:
        if not project.is_drama_workspace:
            return project

        normalized = project.normalized_completed_roles()
        if normalized != list(project.completed_roles or []):
            project.completed_roles = normalized
        project.drama_stage = cls.resolve_current_stage(project)
        project.delivery_status = cls.resolve_delivery_status(project)
        project.quality_scores = cls.extract_quality_scores(project)
        project.progress_percent = min(100, max(0, int(project.get_completion_rate())))
        project.save(
            update_fields=[
                "completed_roles",
                "drama_stage",
                "delivery_status",
                "quality_scores",
                "progress_percent",
                "updated_at",
            ]
        )
        return project

    @classmethod
    def is_deliverable(cls, project: Project) -> bool:
        from apps.creation.artifact_service import get_artifact

        if project.is_drama_workspace:
            return (
                project.delivery_status in ("ready", "delivered")
                or project.drama_stage == DramaStage.DELIVERED
            )
        return bool(get_artifact(project, "episode_scripts"))

    @classmethod
    def deliverable_project_ids(cls):
        return cls.workspace_projects_qs().filter(
            Q(delivery_status__in=("ready", "delivered"))
            | Q(drama_stage=DramaStage.DELIVERED)
        ).values_list("id", flat=True)

    @classmethod
    def has_blocking_failure(cls, project: Project) -> bool:
        if cls.is_deliverable(project):
            return False
        if not project.is_drama_workspace:
            return False
        return DramaRoleExecution.objects.filter(
            project=project,
            status=DramaRoleExecution.Status.FAILED,
        ).exists()

    @classmethod
    def in_progress_project_ids(cls):
        return DramaRoleExecution.objects.filter(
            status=DramaRoleExecution.Status.RUNNING
        ).values_list("project_id", flat=True)

    @classmethod
    def blocked_project_ids(cls):
        failed_pids = DramaRoleExecution.objects.filter(
            status=DramaRoleExecution.Status.FAILED
        ).values_list("project_id", flat=True)
        deliverable = set(cls.deliverable_project_ids())
        return [pid for pid in failed_pids if pid not in deliverable]

    @classmethod
    def drama_stage_label(cls, stage: str) -> str:
        if not stage:
            return ""
        for value, label in DramaStage.choices:
            if value == stage:
                return label
        extras = {"ready": "待交付", "delivered": "已交付"}
        return extras.get(stage, stage)

    @classmethod
    def build_progress_payload(cls, project: Project) -> Dict[str, Any]:
        from apps.creation.agent_runtime.entry_plan import DramaEntryPlan

        track_plan = DramaEntryPlan.resolve(
            track_mode=project.track_mode,
            entry_type="from-scratch",
        )
        phase_map = cls.agent_phase_map(project)
        completed = set(project.completed_roles or [])

        phases_summary = []
        if track_plan.get("phases"):
            for phase in track_plan["phases"]:
                phase_agents = phase.get("agents") or []
                done_count = sum(1 for a in phase_agents if a in completed)
                phases_summary.append({
                    "phase": phase.get("phase"),
                    "label": phase.get("label"),
                    "total_roles": len(phase_agents),
                    "completed_roles": done_count,
                    "is_complete": done_count == len(phase_agents) if phase_agents else False,
                })

        return {
            "project_id": str(project.id),
            "title": project.title or project.theme,
            "theme": project.theme,
            "episode_count": project.episode_count,
            "track_mode": project.track_mode,
            "drama_stage": project.drama_stage,
            "drama_stage_display": project.get_drama_stage_display(),
            "delivery_status": project.delivery_status,
            "completion_rate": project.get_completion_rate(),
            "completed_role_count": len(project.completed_roles or []),
            "total_role_count": len(cls.list_track_agent_ids(project)),
            "track_plan": {
                "entry_type": track_plan.get("entry_type"),
                "label": track_plan.get("label"),
                "description": track_plan.get("description"),
            },
            "phases": phases_summary,
            "agent_phase_map": phase_map,
        }

    @classmethod
    def build_admin_summary(cls, project: Project) -> Dict[str, Any]:
        return {
            "project_id": str(project.id),
            "track_mode": project.track_mode,
            "track_mode_display": project.get_track_mode_display(),
            "drama_stage": project.drama_stage,
            "drama_stage_display": project.get_drama_stage_display(),
            "delivery_status": project.delivery_status,
            "completion_rate": project.get_completion_rate(),
            "completed_roles": list(project.completed_roles or []),
            "total_tokens_used": project.total_tokens_used,
            "total_cost_cents": project.total_cost_cents,
        }

    @classmethod
    def build_trace_payload(cls, project: Project, *, limit: int = 50) -> Dict[str, Any]:
        executions = (
            DramaRoleExecution.objects.filter(project=project)
            .order_by("-created_at")[:limit]
        )
        timeline = []
        for row in reversed(list(executions)):
            timeline.append({
                "execution_id": str(row.id),
                "agent_id": row.agent_id,
                "agent_name_zh": row.agent_name_zh,
                "status": row.status,
                "total_tokens": row.total_tokens,
                "cost_cents": row.cost_cents,
                "elapsed_seconds": row.elapsed_seconds,
                "error_message": row.error_message,
                "started_at": row.started_at.isoformat() if row.started_at else "",
                "finished_at": row.finished_at.isoformat() if row.finished_at else "",
            })
        return {
            **cls.build_admin_summary(project),
            **{
                k: v
                for k, v in cls.build_progress_payload(project).items()
                if k in ("phases", "track_plan", "agent_phase_map", "roles")
            },
            "timeline": timeline,
            "execution_count": len(timeline),
        }

    @classmethod
    def resolve_admin_status(cls, project) -> Tuple[str, str]:
        if project.is_drama_workspace:
            if project.delivery_status == "delivered":
                return "delivered", "已交付"
            if project.delivery_status == "ready":
                return "ready", "待交付"
            return project.drama_stage, project.get_drama_stage_display()

        pct = int(getattr(project, "progress_percent", 0) or 0)
        if pct >= 100:
            return "delivered", "已完成"
        if pct > 0:
            return DramaStage.WRITING, "创作中"
        return DramaStage.STRATEGY, "策划中"

    @classmethod
    def admin_stage_choices(cls) -> List[Dict[str, str]]:
        rows = [
            {"key": stage.value, "label": label}
            for stage, label in DramaStage.choices
        ]
        rows.append({"key": "ready", "label": "待交付"})
        return rows

    @classmethod
    def filter_workspace_projects(
        cls,
        qs,
        *,
        status_filter: str = "",
        track_mode: str = "",
        has_failed_run: bool = False,
    ):
        if track_mode in (DramaTrackMode.FAST, DramaTrackMode.EXPERT):
            qs = qs.filter(track_mode=track_mode)

        if has_failed_run or status_filter == "failed_run":
            failed_pids = DramaRoleExecution.objects.filter(
                status=DramaRoleExecution.Status.FAILED
            ).values_list("project_id", flat=True)
            return qs.filter(id__in=failed_pids)

        if status_filter == "running":
            running_pids = DramaRoleExecution.objects.filter(
                status=DramaRoleExecution.Status.RUNNING
            ).values_list("project_id", flat=True)
            return qs.filter(id__in=running_pids)

        valid_stages = {choice.value for choice in DramaStage}
        if status_filter in valid_stages:
            return qs.filter(drama_stage=status_filter)

        if status_filter == "ready":
            return qs.filter(delivery_status="ready")

        if status_filter == "delivered":
            return qs.filter(delivery_status="delivered")

        return qs

    @classmethod
    def build_admin_facets(cls) -> Dict[str, Any]:
        running_pids = DramaRoleExecution.objects.filter(
            status=DramaRoleExecution.Status.RUNNING
        ).values_list("project_id", flat=True)
        failed_pids = DramaRoleExecution.objects.filter(
            status=DramaRoleExecution.Status.FAILED
        ).values_list("project_id", flat=True)
        drama_qs = cls.workspace_projects_qs()

        return {
            "all": drama_qs.count() or Project.objects.count(),
            "running": len(set(running_pids)),
            "failed": len(set(failed_pids)),
            "awaiting": drama_qs.filter(drama_stage=DramaStage.REVIEW).count(),
            "ready": drama_qs.filter(delivery_status="ready").count(),
            "delivered": drama_qs.filter(delivery_status="delivered").count(),
            "workspace_projects": drama_qs.count(),
            "has_failed_run": len(set(failed_pids)),
            "fast_track": drama_qs.filter(track_mode=DramaTrackMode.FAST).count(),
            "expert_track": drama_qs.filter(track_mode=DramaTrackMode.EXPERT).count(),
        }

    @classmethod
    def dashboard_payload(cls, *, days: int = 30) -> Dict[str, Any]:
        from datetime import timedelta

        from django.db.models import Avg, Count, Q, Sum
        from django.utils import timezone

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        since = today_start - timedelta(days=max(1, days) - 1)

        base_qs = DramaRoleExecution.objects.filter(created_at__gte=since)
        today_qs = base_qs.filter(created_at__gte=today_start)

        def _summary(qs) -> Dict[str, Any]:
            total = qs.count()
            failed = qs.filter(status=DramaRoleExecution.Status.FAILED).count()
            success = qs.filter(status=DramaRoleExecution.Status.SUCCESS).count()
            running = qs.filter(status=DramaRoleExecution.Status.RUNNING).count()
            rate = round(failed / total, 4) if total else 0.0
            avg_elapsed = qs.filter(elapsed_seconds__isnull=False).aggregate(
                avg=Avg("elapsed_seconds")
            )["avg"]
            avg_ms = int(float(avg_elapsed or 0) * 1000)
            tokens = qs.aggregate(total=Sum("total_tokens"))["total"] or 0
            return {
                "run_count": total,
                "completed_count": success,
                "failed_count": failed,
                "running_count": running,
                "failure_rate": rate,
                "avg_duration_ms": avg_ms,
                "total_tokens": int(tokens),
            }

        runs_7d: List[Dict[str, Any]] = []
        for i in range(6, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_qs = DramaRoleExecution.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end,
            )
            runs_7d.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "run_count": day_qs.count(),
                    "completed_count": day_qs.filter(
                        status=DramaRoleExecution.Status.SUCCESS
                    ).count(),
                    "failed_count": day_qs.filter(
                        status=DramaRoleExecution.Status.FAILED
                    ).count(),
                }
            )

        by_role = list(
            base_qs.values("agent_id", "agent_name_zh")
            .annotate(
                run_count=Count("id"),
                success_count=Count(
                    "id", filter=Q(status=DramaRoleExecution.Status.SUCCESS)
                ),
                failed_count=Count(
                    "id", filter=Q(status=DramaRoleExecution.Status.FAILED)
                ),
                total_tokens=Sum("total_tokens"),
                avg_elapsed_seconds=Avg("elapsed_seconds"),
            )
            .order_by("-run_count")[:20]
        )
        for row in by_role:
            total = row["run_count"] or 0
            failed = row["failed_count"] or 0
            row["failure_rate"] = round(failed / total, 4) if total else 0.0
            row["avg_duration_ms"] = int(float(row.get("avg_elapsed_seconds") or 0) * 1000)

        drama_count = cls.workspace_projects_qs().count()
        active_projects = (
            DramaRoleExecution.objects.filter(status=DramaRoleExecution.Status.RUNNING)
            .values("project_id")
            .distinct()
            .count()
        )

        return {
            "summary": {
                "today": _summary(today_qs),
                "period": {**_summary(base_qs), "period_days": days},
            },
            "runs_7d": runs_7d,
            "by_role": by_role,
            "workspace_project_count": drama_count,
            "active_project_count": active_projects,
        }
