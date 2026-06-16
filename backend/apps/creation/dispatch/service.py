# -*- coding: utf-8 -*-
"""TaskDispatchService — 统一任务调度入口

将原来分散在三处的入队逻辑统一收口：
  - auto 模式：run_creation_pipeline
  - step 模式：run_creation_step（触发单节点）
  - workspace 模式：run_creation_step（单技能节点）

外部调用统一走 TaskDispatchService.dispatch()，不再直接 import Celery task。

注意：此 Service 仅负责「任务记录写入 + Celery 入队」，具体执行逻辑仍在
原有 tasks.py / orchestration/ 中，保持现有链路不变，平滑兼容。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from apps.creation.models import CreationTask, Project
from .state_machine import TaskStateMachineError, validate_transition

logger = logging.getLogger(__name__)


class TaskDispatchService:
    """统一任务调度服务

    使用方式：
        task = TaskDispatchService.dispatch(
            project=project,
            trigger_mode=CreationTask.TRIGGER_WORKSPACE,
            node_index=2,
            options={...},
        )
    """

    @classmethod
    def dispatch(
        cls,
        project: "Project",
        trigger_mode: str = CreationTask.TRIGGER_WORKSPACE,
        *,
        node_index: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> CreationTask:
        """创建任务记录并入队到 Celery

        Args:
            project: 所属创作项目
            trigger_mode: auto / step / workspace / retry
            node_index: workspace/step 模式下的目标节点
            options: 传递给 orchestrator 的额外参数

        Returns:
            CreationTask 实例（state=pending）
        """
        options = options or {}
        extra: Dict[str, Any] = {}
        if node_index is not None:
            extra["node_index"] = node_index
        extra.update(options)

        with transaction.atomic():
            task = CreationTask.objects.create(
                project=project,
                workflow=project.pipeline_pack,
                trigger_mode=trigger_mode,
                state=CreationTask.STATE_PENDING,
                extra=extra,
            )

        cls._enqueue(task)
        return task

    @classmethod
    def retry(cls, task: CreationTask) -> CreationTask:
        """对已失败任务发起重试，创建新 Task 记录（不复用旧记录）"""
        new_task = CreationTask.objects.create(
            project=task.project,
            workflow=task.workflow,
            trigger_mode=CreationTask.TRIGGER_RETRY,
            state=CreationTask.STATE_PENDING,
            extra=task.extra,
            retry_count=task.retry_count + 1,
        )
        cls._enqueue(new_task)
        return new_task

    @classmethod
    def cancel(cls, task: CreationTask) -> None:
        """取消任务（仅 pending/paused 可取消）"""
        try:
            validate_transition(task.state, CreationTask.STATE_CANCELLED)
        except TaskStateMachineError as exc:
            raise ValueError(str(exc)) from exc
        task.transition(CreationTask.STATE_CANCELLED)
        logger.info("任务 %s 已取消", task.id)

    @classmethod
    def recover_stale(cls, project: "Project") -> None:
        """恢复卡死的 running 任务为 failed（用于定时巡检或手动触发）"""
        stale_qs = CreationTask.objects.filter(
            project=project,
            state=CreationTask.STATE_RUNNING,
        )
        for task in stale_qs:
            task.transition(
                CreationTask.STATE_FAILED,
                error_code="ERR_STALE_RUNNING",
                error_message="任务长时间处于 running 状态，已被自动标记为失败",
            )
            logger.warning("恢复僵死任务 %s → failed", task.id)

    # ── 内部路由 ──────────────────────────────────────────────

    @classmethod
    def _enqueue(cls, task: CreationTask) -> None:
        """根据 trigger_mode 路由到对应 Celery task"""
        project_id = str(task.project_id)
        extra = task.extra
        node_index = extra.get("node_index")

        try:
            if task.trigger_mode == CreationTask.TRIGGER_AUTO:
                from apps.creation.tasks import run_creation_pipeline
                celery_task = run_creation_pipeline.delay(project_id)
            elif task.trigger_mode in (
                CreationTask.TRIGGER_STEP,
                CreationTask.TRIGGER_WORKSPACE,
                CreationTask.TRIGGER_RETRY,
            ):
                from apps.creation.tasks import run_creation_step
                celery_task = run_creation_step.delay(project_id, node_index)
            else:
                logger.error("未知 trigger_mode: %s", task.trigger_mode)
                task.transition(
                    CreationTask.STATE_FAILED,
                    error_code="ERR_UNKNOWN_MODE",
                    error_message=f"未知触发模式: {task.trigger_mode}",
                )
                return

            task.celery_task_id = celery_task.id
            task.save(update_fields=["celery_task_id", "updated_at"])
        except Exception as exc:  # noqa: BLE001
            logger.exception("入队失败 task=%s: %s", task.id, exc)
            task.transition(
                CreationTask.STATE_FAILED,
                error_code="ERR_ENQUEUE",
                error_message=str(exc),
            )
