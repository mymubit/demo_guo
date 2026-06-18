"""Legacy workflow 异步任务已下线。"""
from __future__ import annotations

from django.tasks import task

from .workflow_engine import LegacyWorkflowRemovedError


@task(queue_name="workflow")
def run_workflow_instance(instance_id: str) -> dict:
    raise LegacyWorkflowRemovedError("run_workflow_instance 已下线")
