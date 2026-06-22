# -*- coding: utf-8 -*-
"""Drama 项目进度 / 阶段 / 轨迹 — 新体系 SSOT。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from django.db.models import Q

from apps.creation.models import Project
from apps.drama.models import DramaProject, DramaRoleExecution

logger = logging.getLogger(__name__)

# 快速通道角色 → 阶段映射
FAST_TRACK_AGENT_PHASE: Dict[str, str] = {
    "drama.topic-planner": DramaProject.Stage.STRATEGY,
    "drama.world-architect": DramaProject.Stage.WORLDBUILDING,
    "drama.character-designer": DramaProject.Stage.WORLDBUILDING,
    "drama.plot-architect": DramaProject.Stage.PLOT_DESIGN,
    "drama.script-writer": DramaProject.Stage.WRITING,
    "drama.script-reviewer": DramaProject.Stage.REVIEW,
    "drama.quality-reporter": DramaProject.Stage.REVIEW,
    "drama.compliance-guard": DramaProject.Stage.COMPLIANCE,
}

DELIVERY_AGENT_IDS = frozenset({"drama.delivery-packer", "drama.compliance-guard"})
QUALITY_AGENT_ID = "drama.quality-reporter"


class DramaProjectProgressService:
    """DramaProject 进度、阶段、交付状态推导与 creation.Project 同步。"""

    @staticmethod
    def find_drama_project(project_ref) -> Optional[DramaProject]:
        """按 DramaProject.id 或 project_id（creation UUID）查找。"""
        try:
            uid = project_ref if isinstance(project_ref, UUID) else UUID(str(project_ref))
        except (TypeError, ValueError):
            return None
        return DramaProject.objects.filter(Q(id=uid) | Q(project_id=uid)).first()

    @staticmethod
    def batch_by_creation_ids(project_ids: List[UUID]) -> Dict[UUID, DramaProject]:
        if not project_ids:
            return {}
        rows = DramaProject.objects.filter(
            Q(project_id__in=project_ids) | Q(id__in=project_ids)
        )
        out: Dict[UUID, DramaProject] = {}
        for dp in rows:
            out[dp.project_id] = dp
            out[dp.id] = dp
        return out

    @classmethod
    def list_track_agent_ids(cls, drama_project: DramaProject) -> List[str]:
        from apps.creation.agent_runtime.entry_plan import DramaEntryPlan

        plan = DramaEntryPlan.resolve(
            track_mode=drama_project.track_mode,
            entry_type="from-scratch",
        )
        if plan.get("recommended_agents"):
            return list(plan["recommended_agents"])
        agents: List[str] = []
        for phase in plan.get("phases") or []:
            agents.extend(phase.get("agents") or [])
        return agents

    @classmethod
    def agent_phase_map(cls, drama_project: DramaProject) -> Dict[str, str]:
        from apps.creation.agent_runtime.entry_plan import DramaEntryPlan

        if drama_project.track_mode == DramaProject.TrackMode.FAST:
            return dict(FAST_TRACK_AGENT_PHASE)

        plan = DramaEntryPlan.resolve(track_mode="expert")
        mapping: Dict[str, str] = {}
        for phase in plan.get("phases") or []:
            phase_code = str(phase.get("phase") or "")
            for agent_id in phase.get("agents") or []:
                mapping[str(agent_id)] = phase_code
        return mapping

    @classmethod
    def resolve_current_stage(cls, drama_project: DramaProject) -> str:
        """根据已完成角色推导当前阶段（最高未完成阶段）。"""
        completed = set(drama_project.completed_roles or [])
        track_agents = cls.list_track_agent_ids(drama_project)
        phase_map = cls.agent_phase_map(drama_project)

        if not track_agents:
            return drama_project.current_stage or DramaProject.Stage.STRATEGY

        # 全部完成 → 已交付
        if all(agent_id in completed for agent_id in track_agents):
            if any(a in completed for a in DELIVERY_AGENT_IDS):
                return DramaProject.Stage.DELIVERED
            return DramaProject.Stage.COMPLIANCE

        for agent_id in track_agents:
            if agent_id not in completed:
                return phase_map.get(agent_id, DramaProject.Stage.STRATEGY)

        return drama_project.current_stage or DramaProject.Stage.STRATEGY

    @classmethod
    def resolve_delivery_status(cls, drama_project: DramaProject) -> str:
        completed = set(drama_project.completed_roles or [])
        if "drama.delivery-packer" in completed:
            return "delivered"
        if DELIVERY_AGENT_IDS & completed:
            return "ready"
        return drama_project.delivery_status or "pending"

    @classmethod
    def extract_quality_scores(cls, drama_project: DramaProject) -> Dict[str, Any]:
        """从 quality-reporter 最近一次成功执行中提取评分。"""
        exec_row = (
            DramaRoleExecution.objects.filter(
                drama_project=drama_project,
                agent_id=QUALITY_AGENT_ID,
                status=DramaRoleExecution.Status.SUCCESS,
            )
            .order_by("-finished_at")
            .first()
        )
        if not exec_row:
            return dict(drama_project.quality_scores or {})

        outputs = exec_row.output_artifacts or {}
        for key in ("quality_report", "score_report", "quality_scores"):
            payload = outputs.get(key)
            if isinstance(payload, dict):
                scores = payload.get("scores") or payload.get("dimensions") or payload
                if isinstance(scores, dict) and scores:
                    merged = dict(drama_project.quality_scores or {})
                    merged.update(scores)
                    if "overall" in payload:
                        merged["overall"] = payload["overall"]
                    return merged
        return dict(drama_project.quality_scores or {})

    @classmethod
    def recompute_project_state(cls, drama_project: DramaProject) -> DramaProject:
        """重算阶段、交付、质量并写库。"""
        drama_project.current_stage = cls.resolve_current_stage(drama_project)
        drama_project.delivery_status = cls.resolve_delivery_status(drama_project)
        drama_project.quality_scores = cls.extract_quality_scores(drama_project)
        drama_project.save(
            update_fields=[
                "current_stage",
                "delivery_status",
                "quality_scores",
                "updated_at",
            ]
        )
        cls.sync_creation_progress(drama_project)
        return drama_project

    @classmethod
    def sync_creation_progress(cls, drama_project: DramaProject) -> None:
        """将 Drama 进度同步至 creation.Project（仅 progress / title）。"""
        try:
            project = Project.objects.get(pk=drama_project.project_id)
        except Project.DoesNotExist:
            return

        project.progress_percent = min(100, max(0, int(drama_project.get_completion_rate())))
        if drama_project.title:
            project.title = drama_project.title
        project.save(update_fields=["progress_percent", "title", "updated_at"])

    @classmethod
    def is_deliverable(cls, project: Project) -> bool:
        """作品可分享/下载。"""
        from apps.creation.artifact_service import get_artifact

        drama = cls.find_drama_project(project.id)
        if drama:
            return (
                drama.delivery_status in ("ready", "delivered")
                or drama.current_stage == DramaProject.Stage.DELIVERED
            )
        return bool(get_artifact(project, "episode_scripts"))

    @classmethod
    def deliverable_project_ids(cls):
        return DramaProject.objects.filter(
            Q(delivery_status__in=("ready", "delivered"))
            | Q(current_stage=DramaProject.Stage.DELIVERED)
        ).values_list("project_id", flat=True)

    @classmethod
    def has_blocking_failure(cls, project: Project) -> bool:
        """存在失败角色执行且尚未交付。"""
        if cls.is_deliverable(project):
            return False
        drama = cls.find_drama_project(project.id)
        if not drama:
            return False
        return DramaRoleExecution.objects.filter(
            drama_project=drama,
            status=DramaRoleExecution.Status.FAILED,
        ).exists()

    @classmethod
    def in_progress_project_ids(cls):
        return DramaRoleExecution.objects.filter(
            status=DramaRoleExecution.Status.RUNNING
        ).values_list("drama_project__project_id", flat=True)

    @classmethod
    def blocked_project_ids(cls):
        failed_pids = DramaRoleExecution.objects.filter(
            status=DramaRoleExecution.Status.FAILED
        ).values_list("drama_project__project_id", flat=True)
        deliverable = set(cls.deliverable_project_ids())
        return [pid for pid in failed_pids if pid not in deliverable]

    @classmethod
    def drama_stage_label(cls, stage: str) -> str:
        if not stage:
            return ""
        for value, label in DramaProject.Stage.choices:
            if value == stage:
                return label
        extras = {"ready": "可交付", "delivered": "已交付"}
        return extras.get(stage, stage)

    @classmethod
    def build_progress_payload(cls, drama_project: DramaProject) -> Dict[str, Any]:
        """组装 /progress/ 接口数据（含轨迹计划）。"""
        from apps.creation.agent_runtime.entry_plan import DramaEntryPlan

        track_plan = DramaEntryPlan.resolve(
            track_mode=drama_project.track_mode,
            entry_type="from-scratch",
        )
        phase_map = cls.agent_phase_map(drama_project)
        completed = set(drama_project.completed_roles or [])

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
            "project_id": str(drama_project.id),
            "creation_project_id": str(drama_project.project_id),
            "title": drama_project.title,
            "track_mode": drama_project.track_mode,
            "current_stage": drama_project.current_stage,
            "current_stage_display": drama_project.get_current_stage_display(),
            "delivery_status": drama_project.delivery_status,
            "completion_rate": drama_project.get_completion_rate(),
            "completed_role_count": len(drama_project.completed_roles or []),
            "total_role_count": len(cls.list_track_agent_ids(drama_project)),
            "track_plan": {
                "entry_type": track_plan.get("entry_type"),
                "label": track_plan.get("label"),
                "description": track_plan.get("description"),
            },
            "phases": phases_summary,
            "agent_phase_map": phase_map,
        }

    @classmethod
    def build_admin_summary(cls, drama_project: DramaProject) -> Dict[str, Any]:
        return {
            "drama_project_id": str(drama_project.id),
            "track_mode": drama_project.track_mode,
            "track_mode_display": drama_project.get_track_mode_display(),
            "current_stage": drama_project.current_stage,
            "current_stage_display": drama_project.get_current_stage_display(),
            "delivery_status": drama_project.delivery_status,
            "completion_rate": drama_project.get_completion_rate(),
            "completed_roles": list(drama_project.completed_roles or []),
            "total_tokens_used": drama_project.total_tokens_used,
            "total_cost_cents": drama_project.total_cost_cents,
        }

    @classmethod
    def build_trace_payload(cls, drama_project: DramaProject, *, limit: int = 50) -> Dict[str, Any]:
        """Admin 轨迹：按 drama 角色时间线。"""
        executions = (
            DramaRoleExecution.objects.filter(drama_project=drama_project)
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
            **cls.build_admin_summary(drama_project),
            **{
                k: v
                for k, v in cls.build_progress_payload(drama_project).items()
                if k in ("phases", "track_plan", "agent_phase_map", "roles")
            },
            "timeline": timeline,
            "execution_count": len(timeline),
        }

    @classmethod
    def resolve_admin_status(cls, project) -> Tuple[str, str]:
        """运营列表/详情状态（Drama 阶段 + 交付态）。"""
        drama = cls.find_drama_project(project.id)
        if drama:
            if drama.delivery_status == "delivered":
                return "delivered", "已交付"
            if drama.delivery_status == "ready":
                return "ready", "可交付"
            return drama.current_stage, drama.get_current_stage_display()

        pct = int(getattr(project, "progress_percent", 0) or 0)
        if pct >= 100:
            return "delivered", "已交付"
        if pct > 0:
            return DramaProject.Stage.WRITING, "剧本创作"
        return DramaProject.Stage.STRATEGY, "战略选题"

    @classmethod
    def admin_stage_choices(cls) -> List[Dict[str, str]]:
        """Admin 筛选项：Drama 阶段 + 交付态。"""
        rows = [
            {"key": stage.value, "label": label}
            for stage, label in DramaProject.Stage.choices
        ]
        rows.append({"key": "ready", "label": "可交付"})
        return rows

    @classmethod
    def filter_creation_projects(
        cls,
        qs,
        *,
        status_filter: str = "",
        track_mode: str = "",
        has_failed_run: bool = False,
    ):
        """Admin 创作项目列表过滤（无 fusion_status）。"""
        from apps.drama.models import DramaRoleExecution

        if track_mode in (DramaProject.TrackMode.FAST, DramaProject.TrackMode.EXPERT):
            drama_pids = DramaProject.objects.filter(track_mode=track_mode).values_list(
                "project_id", flat=True
            )
            qs = qs.filter(id__in=drama_pids)

        if has_failed_run or status_filter == "failed_run":
            failed_pids = DramaRoleExecution.objects.filter(
                status=DramaRoleExecution.Status.FAILED
            ).values_list("drama_project__project_id", flat=True)
            return qs.filter(id__in=failed_pids)

        if status_filter == "running":
            running_pids = DramaRoleExecution.objects.filter(
                status=DramaRoleExecution.Status.RUNNING
            ).values_list("drama_project__project_id", flat=True)
            return qs.filter(id__in=running_pids)

        valid_stages = {choice.value for choice in DramaProject.Stage}
        if status_filter in valid_stages:
            pids = DramaProject.objects.filter(current_stage=status_filter).values_list(
                "project_id", flat=True
            )
            return qs.filter(id__in=pids)

        if status_filter == "ready":
            pids = DramaProject.objects.filter(delivery_status="ready").values_list(
                "project_id", flat=True
            )
            return qs.filter(id__in=pids)

        if status_filter == "delivered":
            pids = DramaProject.objects.filter(delivery_status="delivered").values_list(
                "project_id", flat=True
            )
            return qs.filter(id__in=pids)

        return qs

    @classmethod
    def build_admin_facets(cls) -> Dict[str, Any]:
        """Admin 快捷筛选计数（Drama SSOT）。"""
        from apps.drama.models import DramaRoleExecution

        running_pids = DramaRoleExecution.objects.filter(
            status=DramaRoleExecution.Status.RUNNING
        ).values_list("drama_project__project_id", flat=True)
        failed_pids = DramaRoleExecution.objects.filter(
            status=DramaRoleExecution.Status.FAILED
        ).values_list("drama_project__project_id", flat=True)

        return {
            "all": DramaProject.objects.count() or Project.objects.count(),
            "running": len(set(running_pids)),
            "failed": len(set(failed_pids)),
            "awaiting": DramaProject.objects.filter(
                current_stage=DramaProject.Stage.REVIEW
            ).count(),
            "ready": DramaProject.objects.filter(delivery_status="ready").count(),
            "delivered": DramaProject.objects.filter(delivery_status="delivered").count(),
            "drama_projects": DramaProject.objects.count(),
            "has_failed_run": len(set(failed_pids)),
            "fast_track": DramaProject.objects.filter(track_mode=DramaProject.TrackMode.FAST).count(),
            "expert_track": DramaProject.objects.filter(track_mode=DramaProject.TrackMode.EXPERT).count(),
        }

    @classmethod
    def dashboard_payload(cls, *, days: int = 30) -> Dict[str, Any]:
        """Drama 角色执行监控大盘（Admin Dashboard / Agent 运营）。"""
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

        drama_projects = DramaProject.objects.count()
        active_projects = (
            DramaRoleExecution.objects.filter(status=DramaRoleExecution.Status.RUNNING)
            .values("drama_project_id")
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
            "drama_project_count": drama_projects,
            "active_project_count": active_projects,
        }
