# -*- coding: utf-8 -*-
"""工作流相关的 Celery 任务
========================================================
所有工作流执行统一通过 Celery 任务调度，保证：
  • 与 HTTP 请求解耦（创作过程可能耗时数分钟）
  • 自动重试 / 幂等保护
  • 失败自动告警（监控系统对接）

入口：run_workflow_instance(instance_id, start_node_id=None)
     —— 在 WorkflowScheduler.start_for_project 中被调用
========================================================
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    from celery import shared_task  # type: ignore
except Exception:  # pragma: no cover - Celery 未初始化时的保护
    def shared_task(func):  # type: ignore
        """Celery 未配置时的降级：把任务装饰成可直接调用的函数。"""
        return func


logger = logging.getLogger(__name__)


@shared_task(
    bind=False,
    name="workflow.run_workflow_instance",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
    max_retries=2,
    rate_limit="60/m",
    acks_late=True,
)
def run_workflow_instance(instance_id: str, *, start_node_id: Optional[str] = None) -> str:
    """异步执行一个 WorkflowInstance。

    关键设计：
      • 本任务只读取 DB（instance_id），不接收大 payload，避免 Celery 消息膨胀
      • 内部封装两层 try/except：最外层保证永远不把异常抛回给 Celery（防止无限重试）
      • 内部由 WorkflowEngine 管理节点级别的重试与容错
    """
    logger.info("[task.run_workflow_instance] 开始执行 instance=%s start=%s",
                instance_id, start_node_id)

    try:
        # 延迟导入（避免在 Celery worker 启动时加载不必要的 Django app）
        from apps.workflow.workflow_engine import WorkflowEngine
        from apps.workflow.execution_models import WorkflowInstance

        try:
            instance = WorkflowInstance.objects.get(id=instance_id)
        except WorkflowInstance.DoesNotExist:
            logger.error("[task.run_workflow_instance] instance_id=%s 不存在",
                         instance_id)
            return "not_found"

        engine = WorkflowEngine(instance)
        engine.run(start_node_id=start_node_id)
        logger.info(
            "[task.run_workflow_instance] 完成 instance=%s status=%s",
            instance_id, instance.status,
        )
        return str(instance.status)

    except Exception as exc:
        logger.exception("[task.run_workflow_instance] 致命错误: %s", exc)
        return "fatal_error"


@shared_task(name="workflow.instance_watchdog")
def instance_watchdog() -> None:
    """定时任务：检测"僵尸"实例（长时间 running 且无心跳）。

    触发时机：建议每分钟 1 次（由 Celery Beat / Django Q 调度）。
    策略：
      • 扫描 status=running 且 last_heartbeat_at < now - 10min
      • 写回 failed 状态 + 告警原因
    """
    from django.utils import timezone
    from apps.workflow.execution_models import WorkflowInstance

    stale_threshold = timezone.now() - timezone.timedelta(minutes=10)

    stale_count = WorkflowInstance.objects.filter(
        status="running",
        last_heartbeat_at__lte=stale_threshold,
    ).update(
        status="failed",
        failure_reason="watchdog_timeout:no_heartbeat_for_10min",
        finished_at=timezone.now(),
        updated_at=timezone.now(),
    )

    if stale_count:
        logger.warning("[instance_watchdog] 标记 %d 个僵尸实例为失败", stale_count)


__all__ = ["run_workflow_instance", "instance_watchdog"]
