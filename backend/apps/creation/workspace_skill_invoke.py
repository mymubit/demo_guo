# -*- coding: utf-8 -*-
"""工作台单节点 SkillInvoker 扁平调用（Agent 未注册时的回退路径）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .models import Project


def workspace_node_to_skill_id(node_index: int) -> str:
    """工作台节点索引 → 创作技能 ID。"""
    mapping = {
        1: "creation.brief",
        2: "creation.structure",
        3: "creation.character",
        4: "creation.outline",
        5: "creation.script",
        6: "creation.review",
        7: "creation.polish",
    }
    return mapping.get(int(node_index), "")


@dataclass
class SkillAgentResult:
    """工作台单节点调用结果（轻量版 AgentResult）。"""

    status: str = "completed"
    agent_id: str = ""
    outputs: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "agent_id": self.agent_id,
            "outputs": self.outputs,
            "errors": self.errors,
            "meta": self.meta,
        }


def invoke_workspace_skill_flat(
    project: Project,
    node_index: int,
    *,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    outline_mode: Optional[str] = None,
    outline_stage_key: Optional[str] = None,
) -> SkillAgentResult:
    """扁平路径：SkillInvoker → creation.{node} 技能。"""
    from apps.skill.skills.invoker import get_skill_invoker

    from .skill_invoke_payload import apply_creation_skill_output, build_creation_skill_invoke_payload

    skill_id = workspace_node_to_skill_id(node_index)
    if not skill_id:
        return SkillAgentResult(
            status="error",
            agent_id=f"node-{node_index}",
            errors=[f"节点 {node_index} 未映射到 creation.* 技能"],
        )

    payload = build_creation_skill_invoke_payload(
        project,
        skill_id,
        script_from=script_from,
        script_to=script_to,
        outline_mode=outline_mode,
        outline_stage_key=outline_stage_key,
    )
    skill_result = get_skill_invoker().invoke(
        skill_id=skill_id,
        payload=payload,
        project_id=str(project.id),
        user_id=project.user_id,
    )
    if skill_result.success:
        artifact_key = apply_creation_skill_output(
            project,
            node_index,
            skill_id,
            skill_result.data or {},
        )
        return SkillAgentResult(
            status="completed",
            agent_id=skill_id,
            outputs={**(skill_result.data or {}), "artifact_key": artifact_key},
            meta={
                "skill_id": skill_id,
                "trace_id": skill_result.trace_id,
                "fusion": {
                    "ok": True,
                    "skipped": False,
                    "status": "completed",
                    "artifact_key": artifact_key,
                },
            },
        )
    return SkillAgentResult(
        status="error",
        agent_id=skill_id,
        errors=[skill_result.error.get("message", "skill invoker failed")],
        meta={
            "skill_id": skill_id,
            "trace_id": skill_result.trace_id,
            "fusion": {"ok": False, "skipped": False, "error": skill_result.error.get("message", "")},
        },
    )
