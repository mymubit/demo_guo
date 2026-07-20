# -*- coding: utf-8 -*-
"""Celery 异步任务。"""
from __future__ import annotations

import logging

from celery import chord, group, shared_task

from apps.drama.models import DramaGenerationJob
from apps.drama.services.generation_service import GenerationService, TERMINAL_JOB_STATUSES
from apps.drama.services.llm_provider import LlmProvider, LlmProviderStatus

logger = logging.getLogger(__name__)


def _is_terminal(job: DramaGenerationJob) -> bool:
    return job.status in TERMINAL_JOB_STATUSES


@shared_task(bind=True, max_retries=2)
def run_generation_task(self, job_id: str) -> None:
    GenerationService().execute_generation(job_id)


@shared_task(bind=True, max_retries=2)
def run_external_review_task(self, job_id: str) -> None:
    GenerationService().execute_external_review(job_id)


@shared_task(bind=True)
def _score_subtask(self, job_id: str) -> dict:
    service = GenerationService()
    job = service.get_job(job_id)
    if _is_terminal(job):
        return {}
    try:
        return service._build_quality_report(job, job.request_payload)
    except Exception as exc:
        logger.exception("Quality scoring subtask failed for job %s", job_id)
        detail = str(exc).strip() or exc.__class__.__name__
        if len(detail) > 240:
            detail = detail[:240] + "…"
        service.mark_failed_if_active(job_id, f"评分子任务失败: {detail}")
        raise


@shared_task(bind=True)
def _compliance_subtask(self, job_id: str) -> dict:
    service = GenerationService()
    job = service.get_job(job_id)
    if _is_terminal(job):
        return {}
    try:
        return service._build_compliance_report(job, job.request_payload)
    except Exception as exc:
        logger.exception("Compliance subtask failed for job %s", job_id)
        detail = str(exc).strip() or exc.__class__.__name__
        if len(detail) > 240:
            detail = detail[:240] + "…"
        service.mark_failed_if_active(job_id, f"合规子任务失败: {detail}")
        raise


@shared_task(bind=True)
def _parallel_judge_callback(self, results: list, job_id: str) -> None:
    service = GenerationService()
    job = service.get_job(job_id)
    if _is_terminal(job):
        return
    try:
        score_result, compliance_result = results
        if not score_result or not compliance_result:
            service.mark_failed_if_active(job_id, "并行评审子任务返回空结果")
            return
        service._finalize_quality_results(job, score_result, compliance_result)
    except Exception:
        logger.exception("Parallel judge callback failed for job %s", job_id)
        service.mark_failed_if_active(job_id, "并行评审汇总失败")
        raise


@shared_task(bind=True)
def _parallel_judge_errback(self, request, exc, traceback, job_id: str) -> None:
    logger.exception(
        "Parallel judge chord failed for job %s: %s",
        job_id,
        exc,
        exc_info=exc,
    )
    GenerationService().mark_failed_if_active(job_id, f"并行评审失败: {exc}")


@shared_task(bind=True)
def run_parallel_judge_task(self, job_id: str) -> None:
    """评分与合规并行 group/chord。"""
    service = GenerationService()
    job = service.get_job(job_id)
    if _is_terminal(job):
        return

    service.mark_running(job)

    llm_status = LlmProvider.status()
    if llm_status != LlmProviderStatus.ENABLED:
        service.mark_disabled(job, f"LLM 不可用 ({llm_status.value})")
        return

    workflow = chord(
        group(_score_subtask.s(job_id), _compliance_subtask.s(job_id)),
        _parallel_judge_callback.s(job_id),
    )
    workflow.on_error(_parallel_judge_errback.s(job_id))
    workflow.apply_async()
