# -*- coding: utf-8 -*-
"""V3 异步命令执行（由 Celery task 调用）。"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from django.conf import settings

from apps.drama.models import V3CommandRun, V3Project
from apps.drama.orchestrator.delivery_gate import evaluate_delivery_gate
from apps.drama.skills_bridge.executor import GenerationError, execute_generation
from apps.drama.skills_bridge.recipe_map import recipe_for

_FRIENDLY_FALLBACK = "生成失败，请稍后重试"
_REPORT_COMMANDS = frozenset({"score_quality", "check_compliance"})


def _resolve_llm_call() -> Callable[..., str] | None:
    override = getattr(settings, "V3_LLM_CALL_OVERRIDE", None)
    if override is None:
        return None
    if not callable(override):
        return None
    return override


def _friendly_error(exc: BaseException) -> str:
    if isinstance(exc, GenerationError):
        msg = str(exc).strip()
        return msg or _FRIENDLY_FALLBACK
    msg = str(exc).strip()
    if not msg:
        return _FRIENDLY_FALLBACK
    # 避免把堆栈类信息直接暴露给前端
    if "Traceback" in msg or len(msg) > 240:
        return _FRIENDLY_FALLBACK
    return msg


def _validate_write_episode_batch_payload(request_payload: dict[str, Any]) -> None:
    """校验 write_episode_batch 的 episode_range。"""
    raw = request_payload.get("episode_range")
    if not isinstance(raw, dict):
        raise GenerationError("请指定要撰写的集数范围（episode_range）")
    try:
        start = int(raw.get("start"))
        end = int(raw.get("end"))
    except (TypeError, ValueError) as exc:
        raise GenerationError("集数范围必须是整数起止") from exc
    if start < 1 or end < start:
        raise GenerationError("集数范围无效，请检查起止集号")


def _fail_delivery_gate(run: V3CommandRun, blockers: list[str]) -> None:
    message = "；".join(item for item in blockers if item) or "交付门禁未通过"
    run.status = V3CommandRun.Status.FAILED
    run.error_message = message
    run.result_payload = {"blockers": list(blockers)}
    run.save(
        update_fields=["status", "error_message", "result_payload", "updated_at"]
    )


def _advance_stage_after_success(run: V3CommandRun) -> None:
    """报告成功 writing→quality；交付包成功 → delivery。"""
    project = run.project
    if project is None:
        return
    project.refresh_from_db()
    if run.command_type in _REPORT_COMMANDS:
        if project.stage == V3Project.Stage.WRITING:
            project.stage = V3Project.Stage.QUALITY
            project.save(update_fields=["stage", "updated_at"])
        return
    if run.command_type == "prepare_delivery":
        if project.stage != V3Project.Stage.DELIVERY:
            project.stage = V3Project.Stage.DELIVERY
            project.save(update_fields=["stage", "updated_at"])


def run_v3_command(run_id: UUID | str) -> None:
    """置 running →（可选门禁）→ execute_generation → succeeded/failed。"""
    try:
        run = V3CommandRun.objects.select_related("project").get(id=run_id)
    except V3CommandRun.DoesNotExist:
        return

    if run.project_id is None or run.project is None:
        run.status = V3CommandRun.Status.FAILED
        run.error_message = "命令未绑定项目，无法执行"
        run.save(update_fields=["status", "error_message", "updated_at"])
        return

    run.status = V3CommandRun.Status.RUNNING
    run.error_message = ""
    run.save(update_fields=["status", "error_message", "updated_at"])

    try:
        request_payload = (
            run.request_payload if isinstance(run.request_payload, dict) else {}
        )
        if run.command_type == "write_episode_batch":
            _validate_write_episode_batch_payload(request_payload)

        recipe = recipe_for(run.command_type)
        if recipe.get("requires_delivery_gate"):
            gate = evaluate_delivery_gate(run.project)
            if not gate.get("passed"):
                blockers = gate.get("blockers") or []
                if not isinstance(blockers, list):
                    blockers = []
                _fail_delivery_gate(run, [str(item) for item in blockers])
                return

        created = execute_generation(
            command_type=run.command_type,
            project=run.project,
            run=run,
            llm_call=_resolve_llm_call(),
        )
    except Exception as exc:  # noqa: BLE001 — 任务边界：统一落库人话失败
        run.status = V3CommandRun.Status.FAILED
        run.error_message = _friendly_error(exc)
        run.result_payload = {}
        run.save(update_fields=["status", "error_message", "result_payload", "updated_at"])
        return

    run.status = V3CommandRun.Status.SUCCEEDED
    run.error_message = ""
    run.result_payload = {"artifact_ids": [str(item.id) for item in created]}
    run.save(update_fields=["status", "error_message", "result_payload", "updated_at"])
    _advance_stage_after_success(run)


def enqueue_v3_command(run_id: UUID | str) -> Any:
    """投递 Celery 任务；eager 模式下会同步执行完毕。"""
    from apps.drama.tasks_v3 import run_v3_command_task

    return run_v3_command_task.delay(str(run_id))
