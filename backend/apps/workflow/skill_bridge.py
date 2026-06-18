"""Legacy skill bridge 已下线。"""
from __future__ import annotations

from .workflow_engine import LegacyWorkflowRemovedError


def invoke_skill_for_node(*args, **kwargs):
    raise LegacyWorkflowRemovedError("SkillBridge 已下线")
