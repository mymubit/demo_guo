"""Legacy orchestration adapter 已下线。"""
from __future__ import annotations

from .workflow_engine import LegacyWorkflowRemovedError


def launch_creation_via_workflow(*args, **kwargs):
    raise LegacyWorkflowRemovedError("orchestration adapter 已下线")
