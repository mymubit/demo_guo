# -*- coding: utf-8 -*-
from django.db import transaction

from apps.core.exceptions import BusinessException
from apps.drama.models import V3CommandRun, V3Project
from apps.drama.services.templates_service import resolve_template_seed

from .accept_findings import run_accept_findings_command
from .async_runner import enqueue_v3_command
from .confirm import run_confirm_command
from .provider_test import run_test_model_provider_command
from .types import (
    ASYNC_LIVE_COMMANDS,
    ASYNC_STUB_COMMANDS,
    SYNC_CONFIRM_COMMANDS,
    SYNC_MUTATION_COMMANDS,
    SYNC_PROVIDER_TEST_COMMANDS,
)

_UNSUPPORTED_MESSAGE = "该创作命令将在后续里程碑开放，当前仅完成项目与仪表盘"

_REUSABLE_IDEMPOTENT_STATUSES = frozenset(
    {
        V3CommandRun.Status.QUEUED,
        V3CommandRun.Status.RUNNING,
        V3CommandRun.Status.SUCCEEDED,
    }
)


def _find_reusable_idempotent_run(
    *,
    owner,
    command_type: str,
    idempotency_key: str,
) -> V3CommandRun | None:
    """同 owner + idempotency_key + command_type 才复用；失败态不复用。"""
    key = (idempotency_key or "").strip()
    if not key:
        return None
    return (
        V3CommandRun.objects.filter(
            owner=owner,
            command_type=command_type,
            idempotency_key=key,
            status__in=_REUSABLE_IDEMPOTENT_STATUSES,
        )
        .order_by("-created_at")
        .first()
    )


def _resolve_owned_project(*, owner, payload: dict) -> V3Project | None:
    project_id = (payload or {}).get("project_id")
    if not project_id:
        return None
    try:
        return V3Project.objects.get(id=project_id, owner=owner)
    except (V3Project.DoesNotExist, ValueError, TypeError):
        return None


def _fail_run(run: V3CommandRun, message: str) -> V3CommandRun:
    run.status = V3CommandRun.Status.FAILED
    run.error_message = message
    run.save(update_fields=["status", "error_message", "updated_at"])
    return run


def dispatch_command(
    *,
    owner,
    command_type: str,
    payload: dict,
    idempotency_key: str = "",
) -> V3CommandRun:
    existing = _find_reusable_idempotent_run(
        owner=owner,
        command_type=command_type,
        idempotency_key=idempotency_key,
    )
    if existing is not None:
        return existing

    if command_type == "create_project":
        with transaction.atomic():
            run = V3CommandRun.objects.create(
                owner=owner,
                command_type=command_type,
                status=V3CommandRun.Status.RUNNING,
                idempotency_key=idempotency_key or "",
                request_payload=payload or {},
            )
            title = (payload or {}).get("title") or ""
            entry_type = (payload or {}).get("entry_type") or ""
            if not title or entry_type not in ("original", "adapt"):
                run.status = V3CommandRun.Status.FAILED
                run.error_message = "标题与创作来源（原创/改编）不能为空"
                run.save(update_fields=["status", "error_message", "updated_at"])
                return run
            try:
                template_seed = resolve_template_seed(payload or {})
            except BusinessException as exc:
                run.status = V3CommandRun.Status.FAILED
                run.error_message = exc.message
                run.save(update_fields=["status", "error_message", "updated_at"])
                return run
            project_settings: dict = {}
            if template_seed is not None:
                project_settings["template_seed"] = template_seed
            project = V3Project.objects.create(
                owner=owner,
                title=title[:200],
                entry_type=entry_type,
                stage=V3Project.Stage.TOPIC,
                settings=project_settings,
            )
            run.project = project
            run.status = V3CommandRun.Status.SUCCEEDED
            run.result_payload = {"project_id": str(project.id)}
            run.save(update_fields=["project", "status", "result_payload", "updated_at"])

            # 创建后自动启动选题定调（事务提交后再投递，避免 Celery 读到未提交项目）
            project_id = str(project.id)

            def _auto_generate_topic_brief() -> None:
                dispatch_command(
                    owner=owner,
                    command_type="generate_topic_brief",
                    payload={"project_id": project_id},
                    idempotency_key=f"auto-topic:{project_id}",
                )

            transaction.on_commit(_auto_generate_topic_brief)
            return run

    if command_type in SYNC_CONFIRM_COMMANDS:
        return run_confirm_command(
            owner=owner,
            command_type=command_type,
            payload=payload or {},
            idempotency_key=idempotency_key or "",
        )

    if command_type in SYNC_MUTATION_COMMANDS:
        return run_accept_findings_command(
            owner=owner,
            command_type=command_type,
            payload=payload or {},
            idempotency_key=idempotency_key or "",
        )

    if command_type in SYNC_PROVIDER_TEST_COMMANDS:
        return run_test_model_provider_command(
            owner=owner,
            command_type=command_type,
            payload=payload or {},
            idempotency_key=idempotency_key or "",
        )

    if command_type in ASYNC_LIVE_COMMANDS:
        project = _resolve_owned_project(owner=owner, payload=payload or {})
        run = V3CommandRun.objects.create(
            owner=owner,
            project=project,
            command_type=command_type,
            status=V3CommandRun.Status.QUEUED,
            idempotency_key=idempotency_key or "",
            request_payload=payload or {},
        )
        if project is None:
            return _fail_run(run, "缺少项目或无权访问，请从项目内发起创作命令")
        enqueue_v3_command(run.id)
        run.refresh_from_db()
        return run

    run = V3CommandRun.objects.create(
        owner=owner,
        command_type=command_type,
        status=V3CommandRun.Status.RUNNING,
        idempotency_key=idempotency_key or "",
        request_payload=payload or {},
    )
    if command_type in ASYNC_STUB_COMMANDS:
        run.status = V3CommandRun.Status.UNSUPPORTED
        run.error_message = _UNSUPPORTED_MESSAGE
        run.save(update_fields=["status", "error_message", "updated_at"])
        return run
    run.status = V3CommandRun.Status.FAILED
    run.error_message = "未知命令"
    run.save(update_fields=["status", "error_message", "updated_at"])
    return run
