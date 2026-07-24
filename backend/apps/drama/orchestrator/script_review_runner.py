# -*- coding: utf-8 -*-
"""独立剧本评审异步执行。"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from django.utils import timezone

from apps.drama.models import ScriptReviewRun, V3ArtifactVersion, V3CommandRun
from apps.drama.skills_bridge.executor import GenerationError
from apps.drama.skills_bridge.external_review import execute_external_script_review

_FRIENDLY_FALLBACK = "评审失败，请稍后重试"


def _friendly_error(exc: BaseException) -> str:
    if isinstance(exc, GenerationError):
        msg = str(exc).strip()
        return msg or _FRIENDLY_FALLBACK
    msg = str(exc).strip()
    if not msg:
        return _FRIENDLY_FALLBACK
    if "Traceback" in msg or len(msg) > 240:
        return _FRIENDLY_FALLBACK
    return msg


def _artifact_count_for_project(project_id) -> int:
    if project_id is None:
        return 0
    return V3ArtifactVersion.objects.filter(
        project_id=project_id,
        artifact_key__in=("quality_report", "compliance_report"),
    ).count()


def run_script_review(review_run_id: UUID | str) -> None:
    try:
        review_run = ScriptReviewRun.objects.select_related(
            "review", "review__project", "command_run", "review__owner"
        ).get(id=review_run_id)
    except ScriptReviewRun.DoesNotExist:
        return

    command_run = review_run.command_run
    if command_run is None:
        review_run.status = ScriptReviewRun.Status.FAILED
        review_run.error_message = "缺少命令执行记录"
        review_run.finished_at = timezone.now()
        review_run.save(
            update_fields=["status", "error_message", "finished_at"]
        )
        return

    review = review_run.review
    before_count = _artifact_count_for_project(review.project_id)

    review_run.status = ScriptReviewRun.Status.RUNNING
    review_run.error_message = ""
    review_run.save(update_fields=["status", "error_message"])

    command_run.status = V3CommandRun.Status.RUNNING
    command_run.error_message = ""
    command_run.save(update_fields=["status", "error_message", "updated_at"])

    try:
        report = execute_external_script_review(
            command_type=command_run.command_type,
            review=review,
            run=command_run,
        )
        after_count = _artifact_count_for_project(review.project_id)
        if after_count != before_count:
            raise GenerationError("外界评审禁止写入项目 quality/compliance 产物")

        result_payload: dict[str, Any] = {
            "script_review_id": str(review.id),
            "script_review_run_id": str(review_run.id),
            "kind": review_run.kind,
            "artifact_written": False,
        }
        review_run.status = ScriptReviewRun.Status.SUCCEEDED
        review_run.report_payload = report
        review_run.error_message = ""
        review_run.finished_at = timezone.now()
        review_run.save(
            update_fields=[
                "status",
                "report_payload",
                "error_message",
                "finished_at",
            ]
        )
        command_run.status = V3CommandRun.Status.SUCCEEDED
        command_run.result_payload = result_payload
        command_run.error_message = ""
        command_run.save(
            update_fields=[
                "status",
                "result_payload",
                "error_message",
                "updated_at",
            ]
        )
        review.updated_at = timezone.now()
        review.save(update_fields=["updated_at"])
    except Exception as exc:
        message = _friendly_error(exc)
        review_run.status = ScriptReviewRun.Status.FAILED
        review_run.error_message = message
        review_run.finished_at = timezone.now()
        review_run.save(
            update_fields=["status", "error_message", "finished_at"]
        )
        command_run.status = V3CommandRun.Status.FAILED
        command_run.error_message = message
        command_run.save(
            update_fields=["status", "error_message", "updated_at"]
        )


def enqueue_script_review(review_run_id: UUID | str) -> Any:
    from apps.drama.tasks_v3 import run_script_review_task

    return run_script_review_task.delay(str(review_run_id))
