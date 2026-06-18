"""Legacy workflow 调度已下线。"""
from __future__ import annotations

from .workflow_engine import LegacyWorkflowRemovedError


def schedule_workflow_instance(*args, **kwargs):
    raise LegacyWorkflowRemovedError("workflow 调度已下线")
