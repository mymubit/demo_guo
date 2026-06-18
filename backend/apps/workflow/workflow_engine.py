"""Legacy WorkflowEngine 已下线。"""
from __future__ import annotations


class LegacyWorkflowRemovedError(RuntimeError):
    pass


class WorkflowEngine:
    def __init__(self, *args, **kwargs):
        raise LegacyWorkflowRemovedError("WorkflowEngine 已下线，请使用独立 Agent 工作台")
