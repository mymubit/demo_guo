# -*- coding: utf-8 -*-
"""V3 Celery 任务（与旧 tasks.py 隔离）。"""
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0, name="drama.run_v3_command_task")
def run_v3_command_task(self, run_id: str) -> None:
    from apps.drama.orchestrator.async_runner import run_v3_command

    try:
        run_v3_command(run_id)
    except Exception:
        logger.exception("V3 command task crashed for run_id=%s", run_id)
        raise


@shared_task(bind=True, max_retries=0, name="drama.run_script_review_task")
def run_script_review_task(self, review_run_id: str) -> None:
    from apps.drama.orchestrator.script_review_runner import run_script_review

    try:
        run_script_review(review_run_id)
    except Exception:
        logger.exception(
            "Script review task crashed for review_run_id=%s", review_run_id
        )
        raise
