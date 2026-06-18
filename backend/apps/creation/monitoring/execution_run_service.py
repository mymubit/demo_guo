# -*- coding: utf-8 -*-
"""Agent / 子技能执行追踪：结构化落库并与 LLM 用量关联。"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import timedelta
from typing import Any, Callable, Dict, Iterator, List, Optional

from django.db.models import Avg, Count, Q, Sum
from django.db.models.expressions import ExpressionWrapper, F
from django.db.models.fields import DurationField
from django.utils import timezone

from apps.common.agent_term import alias_agent_id

from ..models import AgentExecutionRun, Project
from ..pipeline_debug_log import summarize_artifact, summarize_upstream

logger = logging.getLogger(__name__)

_active_run_id: ContextVar[Optional[str]] = ContextVar("agent_execution_run_id", default=None)
_order_counter: ContextVar[int] = ContextVar("sub_skill_order", default=0)


def get_active_run_id() -> Optional[str]:
    return _active_run_id.get()


def summarize_sub_skill_output(skill_id: str, payload: Any) -> Dict[str, Any]:
    if payload is None:
        return {"skillId": skill_id, "empty": True}
    if isinstance(payload, dict):
        if "passed" in payload or "issues" in payload or "errors" in payload:
            issues = payload.get("issues") or payload.get("errors") or []
            return {
                "skillId": skill_id,
                "passed": payload.get("passed", payload.get("ok")),
                "issueCount": len(issues) if isinstance(issues, list) else 0,
            }
        keys = sorted(payload.keys())
        return {"skillId": skill_id, "topKeys": keys[:16], "keyCount": len(keys)}
    if isinstance(payload, list):
        return {"skillId": skill_id, "listLen": len(payload)}
    return {"skillId": skill_id, "type": type(payload).__name__}


class AgentExecutionRunService:
    @staticmethod
    def begin_run(
        project: Project,
        *,
        agent_id: str,
        node_index: Optional[int] = None,
        script_from: Optional[int] = None,
        script_to: Optional[int] = None,
        outline_mode: Optional[str] = None,
        input_summary: Optional[Dict[str, Any]] = None,
        agent_version: str = "",
        prompt_version: str = "",
        input_artifact_keys: Optional[List[str]] = None,
        output_artifact_keys: Optional[List[str]] = None,
        input_snapshot: Optional[Dict[str, Any]] = None,
        rendered_prompt_preview: str = "",
        estimated_prompt_tokens: Optional[int] = None,
        model_name: str = "",
        provider_name: str = "",
        started_by: str = "user",
        run_params: Optional[Dict[str, Any]] = None,
        overwrite_mode: str = "replace",
    ) -> AgentExecutionRun:
        return AgentExecutionRun.objects.create(
            project=project,
            user_id=project.user_id,
            agent_id=agent_id or "unknown",
            node_index=int(node_index) if node_index is not None else None,
            status=AgentExecutionRun.STATUS_RUNNING,
            batch_from=script_from,
            batch_to=script_to,
            outline_mode=str(outline_mode or "")[:32],
            input_summary=dict(input_summary or {}),
            agent_version=str(agent_version or "")[:32],
            prompt_version=str(prompt_version or "")[:32],
            input_artifact_keys=list(input_artifact_keys or []),
            output_artifact_keys=list(output_artifact_keys or []),
            input_snapshot=dict(input_snapshot or {}),
            rendered_prompt_preview=str(rendered_prompt_preview or "")[:12000],
            estimated_prompt_tokens=estimated_prompt_tokens,
            model_name=str(model_name or "")[:128],
            provider_name=str(provider_name or "")[:128],
            started_by=str(started_by or "user")[:16],
            run_params=dict(run_params or {}),
            overwrite_mode=str(overwrite_mode or "replace")[:16],
        )

    @staticmethod
    @contextmanager
    def run_scope(
        project: Project,
        *,
        agent_id: str,
        node_index: Optional[int] = None,
        script_from: Optional[int] = None,
        script_to: Optional[int] = None,
        outline_mode: Optional[str] = None,
        input_summary: Optional[Dict[str, Any]] = None,
        agent_version: str = "",
        prompt_version: str = "",
        input_artifact_keys: Optional[List[str]] = None,
        output_artifact_keys: Optional[List[str]] = None,
        input_snapshot: Optional[Dict[str, Any]] = None,
        rendered_prompt_preview: str = "",
        estimated_prompt_tokens: Optional[int] = None,
        model_name: str = "",
        provider_name: str = "",
        started_by: str = "user",
        run_params: Optional[Dict[str, Any]] = None,
        overwrite_mode: str = "replace",
    ) -> Iterator[AgentExecutionRun]:
        run = AgentExecutionRunService.begin_run(
            project,
            agent_id=agent_id,
            node_index=node_index,
            script_from=script_from,
            script_to=script_to,
            outline_mode=outline_mode,
            input_summary=input_summary,
            agent_version=agent_version,
            prompt_version=prompt_version,
            input_artifact_keys=input_artifact_keys,
            output_artifact_keys=output_artifact_keys,
            input_snapshot=input_snapshot,
            rendered_prompt_preview=rendered_prompt_preview,
            estimated_prompt_tokens=estimated_prompt_tokens,
            model_name=model_name,
            provider_name=provider_name,
            started_by=started_by,
            run_params=run_params,
            overwrite_mode=overwrite_mode,
        )
        run_token = _active_run_id.set(str(run.id))
        order_token = _order_counter.set(0)
        try:
            yield run
        except Exception as exc:  # noqa: BLE001
            if run.status == AgentExecutionRun.STATUS_RUNNING:
                AgentExecutionRunService.finish_run(
                    run,
                    AgentExecutionRun.STATUS_FAILED,
                    error_message=str(exc)[:500],
                )
            raise
        finally:
            _active_run_id.reset(run_token)
            _order_counter.reset(order_token)

    @staticmethod
    def finish_run(
        run: AgentExecutionRun,
        status: str,
        *,
        agent_result: Any = None,
        output_artifact_key: str = "",
        output_summary: Optional[Dict[str, Any]] = None,
        error_message: str = "",
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        model_name: str = "",
        provider_name: str = "",
    ) -> AgentExecutionRun:
        if run.status != AgentExecutionRun.STATUS_RUNNING:
            return run

        trace_entries: List[Dict[str, Any]] = []
        if agent_result is not None:
            meta = getattr(agent_result, "meta", None) or {}
            if isinstance(meta, dict):
                trace_entries = list(meta.get("execution_trace") or [])

        # SubSkillExecutionLog 已停写（Legacy 编排专用）

        updates: Dict[str, Any] = {
            "status": status,
            "finished_at": timezone.now(),
            "error_message": str(error_message or "")[:2000],
        }
        if output_artifact_key:
            updates["output_artifact_key"] = output_artifact_key[:64]
        if output_summary is not None:
            updates["output_summary"] = output_summary
        if prompt_tokens is not None:
            updates["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            updates["completion_tokens"] = completion_tokens
        if total_tokens is not None:
            updates["total_tokens"] = total_tokens
        if model_name:
            updates["model_name"] = str(model_name)[:128]
        if provider_name:
            updates["provider_name"] = str(provider_name)[:128]

        for field, value in updates.items():
            setattr(run, field, value)
        run.save(update_fields=list(updates.keys()))
        if status == AgentExecutionRun.STATUS_FAILED:
            try:
                from apps.monitoring.services.task_error import record_agent_execution_failure

                record_agent_execution_failure(run, error_message=updates["error_message"])
            except Exception as exc:  # noqa: BLE001
                logger.warning("[AgentLog] monitoring failure write skipped: %s", exc)
        return run

    @staticmethod
    def sync_sub_skills_from_trace(
        run: AgentExecutionRun,
        trace_entries: List[Dict[str, Any]],
    ) -> None:
        return

    @staticmethod
    def record_sub_skill(
        skill_id: str,
        status: str,
        *,
        skill_type: str = "",
        cli: str = "",
        script: str = "",
        message: str = "",
        input_summary: Optional[Dict[str, Any]] = None,
        output_summary: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        node_id: str = "",
        upstream: Optional[Dict[str, Any]] = None,
        output_payload: Any = None,
        input_payload: Optional[Dict[str, Any]] = None,
        llm_io: Optional[Dict[str, Any]] = None,
    ) -> None:
        return

    @staticmethod
    @contextmanager
    def sub_skill_step(
        skill_id: str,
        *,
        node_id: str = "",
        upstream: Optional[Dict[str, Any]] = None,
        skill_type: str = "",
        cli: str = "",
        script: str = "",
    ) -> Iterator[None]:
        started = time.monotonic()
        try:
            yield
        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.monotonic() - started) * 1000)
            AgentExecutionRunService.record_sub_skill(
                skill_id,
                "failed",
                skill_type=skill_type,
                cli=cli,
                script=script,
                message=str(exc)[:200],
                duration_ms=duration_ms,
                node_id=node_id,
                upstream=upstream,
            )
            raise
        else:
            duration_ms = int((time.monotonic() - started) * 1000)
            AgentExecutionRunService.record_sub_skill(
                skill_id,
                "executed",
                skill_type=skill_type,
                cli=cli,
                script=script,
                duration_ms=duration_ms,
                node_id=node_id,
                upstream=upstream,
            )

    @staticmethod
    def build_output_summary(project: Project, artifact_key: str) -> Dict[str, Any]:
        if not artifact_key:
            return {}
        from ..artifact_service import get_artifact

        payload = get_artifact(project, artifact_key) or {}
        return summarize_artifact(artifact_key, payload if isinstance(payload, dict) else {})

    @staticmethod
    def infer_output_artifact_key(agent_id: str, agent_result: Any) -> str:
        outputs = getattr(agent_result, "outputs", None) or {}
        registry_outputs: List[str] = []
        from apps.agent.runtime import get_agent, primary_output_artifact

        registry_outputs: List[str] = []
        try:
            agent = get_agent(agent_id) or {}
            registry_outputs = [
                str(item)
                for item in (agent.get("outputs") or [])
                if isinstance(item, str) and item.strip()
            ]
        except Exception:  # noqa: BLE001
            pass

        fallback = registry_outputs[0] if registry_outputs else primary_output_artifact(agent_id)

        if not isinstance(outputs, dict):
            return fallback[:64]
        if outputs.get("artifact_key"):
            return str(outputs["artifact_key"])[:64]
        for key in registry_outputs:
            if key in outputs:
                return key[:64]
        default_key = fallback
        if default_key and default_key in outputs:
            return default_key
        for key in outputs:
            if key.endswith("_report") or key.endswith("_log") or key.endswith("_kit"):
                return str(key)[:64]
        return default_key

    @staticmethod
    def summarize_agent_result(agent_id: str, agent_result: Any) -> Dict[str, Any]:
        outputs = getattr(agent_result, "outputs", None) or {}
        meta = getattr(agent_result, "meta", None) or {}
        summary: Dict[str, Any] = {
            "skillId": agent_id,
            "resultStatus": getattr(agent_result, "status", ""),
        }
        if isinstance(outputs, dict) and outputs:
            summary["outputKeys"] = sorted(outputs.keys())[:12]
        if isinstance(meta, dict) and meta.get("suggestion_count") is not None:
            summary["suggestionCount"] = meta.get("suggestion_count")
        if isinstance(meta, dict) and meta.get("reason"):
            summary["reason"] = meta.get("reason")
        return summary

    @staticmethod
    def map_result_status(agent_result: Any) -> str:
        status = str(getattr(agent_result, "status", "") or "")
        if status == "error":
            return AgentExecutionRun.STATUS_FAILED
        return AgentExecutionRun.STATUS_COMPLETED

    @staticmethod
    def run_tracked_agent(
        project: Project,
        agent_id: str,
        runner: Callable[..., Any],
        *,
        node_index: Optional[int] = None,
        script_from: Optional[int] = None,
        script_to: Optional[int] = None,
        outline_mode: Optional[str] = None,
        input_summary: Optional[Dict[str, Any]] = None,
        **runner_kwargs: Any,
    ) -> Any:
        from .agent_execution_log import (
            EVENT_AGENT_END,
            EVENT_AGENT_START,
            LEVEL_ERROR,
            LEVEL_INFO,
            enrich_run_tracked_agent_result,
            event_buffer_scope,
            flush_buffer_to_db,
            log_event,
        )

        with AgentExecutionRunService.run_scope(
            project,
            agent_id=agent_id,
            node_index=node_index,
            script_from=script_from,
            script_to=script_to,
            outline_mode=outline_mode,
            input_summary=input_summary,
        ) as run:
            log_event(
                EVENT_AGENT_START, agent_id, project.id,
                message=f"{agent_id} 开始执行",
                runId=str(run.id),
            )
            _t0 = time.monotonic()

            with event_buffer_scope() as buf:
                result = runner(project, **runner_kwargs)
                duration_ms = int((time.monotonic() - _t0) * 1000)

                # 自动发送输出结构化事件
                try:
                    enrich_run_tracked_agent_result(project.id, agent_id, result, buf)
                except Exception as _exc:  # noqa: BLE001
                    logger.warning("[AgentLog] enrich 失败: %s", _exc)

                log_event(
                    EVENT_AGENT_END, agent_id, project.id,
                    message=f"{agent_id} 执行完成 status={getattr(result, 'status', '?')}",
                    level=LEVEL_ERROR if getattr(result, "status", "") == "error" else LEVEL_INFO,
                    duration_ms=duration_ms,
                    status=getattr(result, "status", ""),
                    runId=str(run.id),
                )

                artifact_key = AgentExecutionRunService.infer_output_artifact_key(agent_id, result)
                output_summary = (
                    AgentExecutionRunService.build_output_summary(project, artifact_key)
                    if artifact_key
                    else AgentExecutionRunService.summarize_agent_result(agent_id, result)
                )
                errors = getattr(result, "errors", None) or []
                error_message = "; ".join(str(e) for e in errors)[:500] if errors else ""
                AgentExecutionRunService.finish_run(
                    run,
                    AgentExecutionRunService.map_result_status(result),
                    agent_result=result,
                    output_artifact_key=artifact_key,
                    output_summary=output_summary,
                    error_message=error_message,
                )

                # 将关键事件持久化到 DB（非阻塞，失败不影响主流程）
                try:
                    flush_buffer_to_db(str(run.id), buf)
                except Exception as _exc:  # noqa: BLE001
                    logger.warning("[AgentLog] flush_buffer_to_db 失败: %s", _exc)

            return result

    @staticmethod
    def serialize_sub_skill(log) -> Dict[str, Any]:
        return {}

    @staticmethod
    def sanitize_input_snapshot(snapshot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Portal 用：仅保留输入键名与运行参数，不返回完整 artifact 内容。"""
        raw = snapshot if isinstance(snapshot, dict) else {}
        artifacts = raw.get("artifacts") if isinstance(raw.get("artifacts"), dict) else {}
        return {
            "required_artifacts": list(raw.get("required_artifacts") or []),
            "input_artifact_keys": list(artifacts.keys()),
            "params": dict(raw.get("params") or {}),
        }

    @staticmethod
    def serialize_run(
        run: AgentExecutionRun,
        *,
        include_sub_skills: bool = False,
        include_sensitive: bool = False,
    ) -> Dict[str, Any]:
        duration_ms = None
        if run.started_at and run.finished_at:
            duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
        input_snapshot = (
            run.input_snapshot or {}
            if include_sensitive
            else AgentExecutionRunService.sanitize_input_snapshot(run.input_snapshot)
        )
        payload: Dict[str, Any] = {
            "id": str(run.id),
            "agent_id": run.agent_id,
            "node_index": run.node_index,
            "status": run.status,
            "batch_from": run.batch_from,
            "batch_to": run.batch_to,
            "outline_mode": run.outline_mode,
            "input_summary": run.input_summary or {},
            "output_summary": run.output_summary or {},
            "output_artifact_key": run.output_artifact_key,
            "agent_version": run.agent_version,
            "prompt_version": run.prompt_version,
            "input_artifact_keys": run.input_artifact_keys or [],
            "output_artifact_keys": run.output_artifact_keys or [],
            "prompt_tokens": run.prompt_tokens,
            "completion_tokens": run.completion_tokens,
            "total_tokens": run.total_tokens,
            "estimated_prompt_tokens": run.estimated_prompt_tokens,
            "model_name": run.model_name,
            "provider_name": run.provider_name,
            "started_by": run.started_by,
            "run_params": run.run_params or {},
            "overwrite_mode": run.overwrite_mode,
            "error_message": run.error_message,
            "input_snapshot": input_snapshot,
            "started_at": run.started_at.isoformat() if run.started_at else "",
            "finished_at": run.finished_at.isoformat() if run.finished_at else "",
            "duration_ms": duration_ms,
        }
        if include_sensitive:
            payload["rendered_prompt_preview"] = (run.rendered_prompt_preview or "")[:8000]
        if include_sub_skills:
            payload.update({"sub_skills": [], "execution_trace": []})
        return alias_agent_id(payload)

    @staticmethod
    def list_recent_runs_global(*, limit: int = 40) -> Dict[str, Any]:
        from apps.workflow.step_admin import PipelineStepAdminService

        limit = max(1, min(limit, 100))
        runs = (
            AgentExecutionRun.objects.select_related("project")
            .order_by("-started_at")[:limit]
        )
        steps = PipelineStepAdminService.list_steps()
        index_to_node_id = {
            int(row.get("node_index") or 0): str(row.get("node_id") or "")
            for row in steps
            if row.get("node_index") is not None
        }
        agent_to_node_id = {
            str(row.get("agent_id") or ""): str(row.get("node_id") or "")
            for row in steps
            if row.get("agent_id")
        }

        items: List[Dict[str, Any]] = []
        node_states: Dict[str, str] = {}
        for run in runs:
            node_id = ""
            if run.node_index is not None:
                node_id = index_to_node_id.get(int(run.node_index), "")
            if not node_id:
                node_id = agent_to_node_id.get(str(run.agent_id or ""), "")
            payload = AgentExecutionRunService.compact_run_summary(run)
            payload.update(
                {
                    "project_id": str(run.project_id),
                    "project_title": getattr(run.project, "title", "") or "",
                    "fusion_node_id": node_id,
                }
            )
            items.append(payload)
            if node_id and node_id not in node_states:
                status = str(run.status or "")
                if status == AgentExecutionRun.STATUS_RUNNING:
                    node_states[node_id] = "running"
                elif status == AgentExecutionRun.STATUS_FAILED:
                    node_states[node_id] = "failed"
                elif status in (AgentExecutionRun.STATUS_COMPLETED, AgentExecutionRun.STATUS_PARTIAL):
                    node_states[node_id] = "completed"
                else:
                    node_states[node_id] = "idle"

        return {"runs": items, "node_states": node_states, "limit": limit}

    @staticmethod
    def list_runs_for_project(
        project: Project,
        *,
        limit: int = 40,
        agent_id: Optional[str] = None,
        node_index: Optional[int] = None,
        include_sensitive: bool = False,
    ) -> List[Dict[str, Any]]:
        qs = AgentExecutionRun.objects.filter(project=project)
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        if node_index is not None:
            qs = qs.filter(node_index=node_index)
        runs = qs.order_by("-started_at")[: max(1, min(limit, 200))]
        return [
            AgentExecutionRunService.serialize_run(run, include_sensitive=include_sensitive)
            for run in runs
        ]

    @staticmethod
    def latest_run_for_agent(
        project: Project,
        *,
        agent_id: Optional[str] = None,
        node_index: Optional[int] = None,
        include_sensitive: bool = False,
    ) -> Optional[Dict[str, Any]]:
        qs = AgentExecutionRun.objects.filter(project=project)
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        if node_index is not None:
            qs = qs.filter(node_index=node_index)
        run = qs.order_by("-started_at").first()
        if not run:
            return None
        return AgentExecutionRunService.serialize_run(run, include_sensitive=include_sensitive)

    @staticmethod
    def compact_run_summary(run: AgentExecutionRun) -> Dict[str, Any]:
        duration_ms = None
        if run.started_at and run.finished_at:
            duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
        return alias_agent_id({
            "id": str(run.id),
            "agent_id": run.agent_id,
            "node_index": run.node_index,
            "status": run.status,
            "output_artifact_key": run.output_artifact_key or "",
            "error_message": (run.error_message or "")[:160],
            "started_at": run.started_at.isoformat() if run.started_at else "",
            "duration_ms": duration_ms,
        })

    @staticmethod
    def batch_project_execution_summary(project_ids: List[Any]) -> Dict[str, Dict[str, Any]]:
        if not project_ids:
            return {}
        runs = AgentExecutionRun.objects.filter(project_id__in=project_ids).order_by(
            "project_id", "-started_at"
        )
        latest_by_project: Dict[str, Dict[str, Any]] = {}
        latest_failed_by_project: Dict[str, Dict[str, Any]] = {}
        run_counts: Dict[str, int] = {}
        failed_counts: Dict[str, int] = {}

        for run in runs:
            pid = str(run.project_id)
            run_counts[pid] = run_counts.get(pid, 0) + 1
            if run.status == AgentExecutionRun.STATUS_FAILED:
                failed_counts[pid] = failed_counts.get(pid, 0) + 1
            if pid not in latest_by_project:
                latest_by_project[pid] = AgentExecutionRunService.compact_run_summary(run)
            if run.status == AgentExecutionRun.STATUS_FAILED and pid not in latest_failed_by_project:
                latest_failed_by_project[pid] = AgentExecutionRunService.compact_run_summary(run)

        out: Dict[str, Dict[str, Any]] = {}
        for raw_id in project_ids:
            pid = str(raw_id)
            out[pid] = {
                "run_count": run_counts.get(pid, 0),
                "failed_count": failed_counts.get(pid, 0),
                "latest_run": latest_by_project.get(pid),
                "latest_failed_run": latest_failed_by_project.get(pid),
            }
        return out

    @staticmethod
    def serialize_llm_usage(log) -> Dict[str, Any]:
        return {
            "id": str(log.id),
            "model_name": log.model_name,
            "provider_name": log.provider_name,
            "sub_skill_id": log.sub_skill_id or "",
            "source_key": log.source_key,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.total_tokens,
            "estimated_input_cost_yuan": float(log.estimated_input_cost_yuan or 0),
            "estimated_output_cost_yuan": float(log.estimated_output_cost_yuan or 0),
            "estimated_cost_yuan": float(log.estimated_cost_yuan or 0),
            "success": log.success,
            "request_payload": log.request_payload or {},
            "response_payload": log.response_payload or {},
            "created_at": log.created_at.isoformat() if log.created_at else "",
        }

    @staticmethod
    def get_run_detail(
        run_id: str,
        *,
        include_sensitive: bool = True,
        include_sub_skills: bool = False,
    ) -> Optional[Dict[str, Any]]:
        from apps.skill.models import LlmUsageLog

        try:
            run = AgentExecutionRun.objects.select_related("project", "user").get(id=run_id)
        except AgentExecutionRun.DoesNotExist:
            return None

        payload = AgentExecutionRunService.serialize_run(
            run,
            include_sensitive=include_sensitive,
            include_sub_skills=include_sub_skills,
        )
        payload["project_id"] = str(run.project_id)
        payload["project_title"] = (run.project.title or run.project.theme or "")[:200]
        payload["user_phone"] = getattr(run.user, "phone", "") or ""

        llm_qs = LlmUsageLog.objects.filter(execution_run_id=run.id).order_by("-created_at")
        llm_agg = llm_qs.aggregate(
            call_count=Count("id"),
            prompt_tokens=Sum("prompt_tokens"),
            completion_tokens=Sum("completion_tokens"),
            total_tokens=Sum("total_tokens"),
            estimated_input_cost_yuan=Sum("estimated_input_cost_yuan"),
            estimated_output_cost_yuan=Sum("estimated_output_cost_yuan"),
            estimated_cost_yuan=Sum("estimated_cost_yuan"),
        )
        payload["llm_usage"] = [
            AgentExecutionRunService.serialize_llm_usage(row) for row in llm_qs[:50]
        ]
        payload["llm_summary"] = {
            "call_count": llm_agg["call_count"] or 0,
            "prompt_tokens": int(llm_agg["prompt_tokens"] or 0),
            "completion_tokens": int(llm_agg["completion_tokens"] or 0),
            "total_tokens": int(llm_agg["total_tokens"] or 0),
            "estimated_input_cost_yuan": float(llm_agg["estimated_input_cost_yuan"] or 0),
            "estimated_output_cost_yuan": float(llm_agg["estimated_output_cost_yuan"] or 0),
            "estimated_cost_yuan": float(llm_agg["estimated_cost_yuan"] or 0),
        }
        return payload

    @staticmethod
    def dashboard_payload(*, days: int = 30) -> Dict[str, Any]:
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        since = today_start - timedelta(days=max(1, days) - 1)

        base_qs = AgentExecutionRun.objects.filter(started_at__gte=since)
        today_qs = base_qs.filter(started_at__gte=today_start)

        def _summary(qs):
            total = qs.count()
            failed = qs.filter(status=AgentExecutionRun.STATUS_FAILED).count()
            completed = qs.filter(status=AgentExecutionRun.STATUS_COMPLETED).count()
            running = qs.filter(status=AgentExecutionRun.STATUS_RUNNING).count()
            rate = round(failed / total, 4) if total else 0.0
            duration_qs = qs.filter(finished_at__isnull=False).annotate(
                duration=ExpressionWrapper(
                    F("finished_at") - F("started_at"),
                    output_field=DurationField(),
                )
            )
            avg_duration = duration_qs.aggregate(avg=Avg("duration"))["avg"]
            avg_ms = int(avg_duration.total_seconds() * 1000) if avg_duration else 0
            return {
                "run_count": total,
                "completed_count": completed,
                "failed_count": failed,
                "running_count": running,
                "failure_rate": rate,
                "avg_duration_ms": avg_ms,
            }

        runs_7d: List[Dict[str, Any]] = []
        for i in range(6, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_qs = AgentExecutionRun.objects.filter(
                started_at__gte=day_start,
                started_at__lt=day_end,
            )
            runs_7d.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "run_count": day_qs.count(),
                    "completed_count": day_qs.filter(
                        status=AgentExecutionRun.STATUS_COMPLETED
                    ).count(),
                    "failed_count": day_qs.filter(
                        status=AgentExecutionRun.STATUS_FAILED
                    ).count(),
                }
            )

        agent_rows = (
            base_qs.values("agent_id")
            .annotate(
                run_count=Count("id"),
                failed_count=Count("id", filter=Q(status=AgentExecutionRun.STATUS_FAILED)),
                avg_duration=Avg(
                    ExpressionWrapper(
                        F("finished_at") - F("started_at"),
                        output_field=DurationField(),
                    ),
                    filter=Q(finished_at__isnull=False),
                ),
            )
            .order_by("-run_count")[:12]
        )
        agent_stats = []
        for row in agent_rows:
            avg = row.get("avg_duration")
            avg_ms = int(avg.total_seconds() * 1000) if avg else 0
            total = row["run_count"] or 0
            failed = row["failed_count"] or 0
            agent_stats.append(
                alias_agent_id(
                    {
                        "agent_id": row["agent_id"],
                        "run_count": total,
                        "failed_count": failed,
                        "failure_rate": round(failed / total, 4) if total else 0.0,
                        "avg_duration_ms": avg_ms,
                    }
                )
            )

        top_failed_sub_skills: List[Dict[str, Any]] = []

        return {
            "summary": {
                "today": _summary(today_qs),
                "period": {**_summary(base_qs), "period_days": days},
            },
            "runs_7d": runs_7d,
            "agent_stats": agent_stats,
            "top_failed_sub_skills": top_failed_sub_skills,
        }
