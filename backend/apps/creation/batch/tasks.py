# -*- coding: utf-8 -*-
"""
批量创作 Celery 任务。
"""

from django.tasks import task

from .services import BatchExecutionConsumer


@task(queue_name="creation")
def process_batch_item(batch_project_id: str) -> dict:
    """
    处理单个批量子项目。

    Args:
        batch_project_id: BatchProject ID

    Returns:
        dict: 执行结果
    """
    return BatchExecutionConsumer.process_batch_item(batch_project_id)
