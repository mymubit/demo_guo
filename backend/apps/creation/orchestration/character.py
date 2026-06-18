# -*- coding: utf-8 -*-
"""CharacterAgent：节点 3 人设开发（registry sub_skills 编排）。"""
from __future__ import annotations

import logging
from typing import List

from ..artifact_service import save_artifact
from ..character_enrichment import normalize_character_bible_payload
from ..ip_lock import merge_character_ip_lock
from ..models import Project
from ..workspace.workspace_editor import _mark_skill_has_content
from .agent_common import build_standard_upstream, deep_merge, load_project_brief
from .agent_detection import run_character_gate
from .agent_llm import run_sub_skill_llm
from .agent_payload import coerce_character_chunk, unwrap_llm_payload
from .sub_skill_runner import (
    agent_execution_meta,
    inject_knowledge_upstream,
    mark_executed,
    persist_execution_trace,
)
from .types import AgentResult

logger = logging.getLogger(__name__)

AGENT_ID = "character"
FUSION_NODE_ID = "node-3-character"
NODE_INDEX = 3

_LLM_SUB_SKILLS = ("character-generator", "relationship-weaver")


def _seed_character_bible(project, brief: dict) -> dict:
    return {
        "nodeId": FUSION_NODE_ID,
        "projectId": str(project.id),
        "workingTitle": brief.get("workingTitle") or project.title or "",
    }


def _merge_character_output(bible: dict, sub_skill_id: str, raw: object) -> dict:
    chunk = unwrap_llm_payload(sub_skill_id, raw)
    if sub_skill_id == "relationship-weaver":
        chunk = coerce_character_chunk(chunk)
        rels = chunk.get("relationshipMap") or chunk.get("relationships") or []
        if rels:
            bible["relationshipMap"] = rels
        if chunk.get("relationshipSummary"):
            bible["relationshipSummary"] = chunk["relationshipSummary"]
        for key in ("characters", "protagonists", "antagonists", "supportingRoles"):
            if chunk.get(key):
                bible = deep_merge(bible, {key: chunk[key]})
        return bible
    chunk = coerce_character_chunk(chunk)
    return deep_merge(bible, chunk)


def run_character_agent(project: Project, *, node_index: int = NODE_INDEX, **_kwargs) -> AgentResult:
    executed: List[str] = []
    errors: List[str] = []

    brief = load_project_brief(project)
    upstream = build_standard_upstream(project, brief)
    bible = _seed_character_bible(project, brief)

    try:
        upstream = inject_knowledge_upstream(AGENT_ID, upstream, project)
        mark_executed(executed, "reference-injector")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[CharacterAgent] reference-injector skipped: %s", exc)

    for sub_skill_id in _LLM_SUB_SKILLS:
        try:
            raw = run_sub_skill_llm(
                project,
                agent_id=AGENT_ID,
                fusion_node_id=FUSION_NODE_ID,
                sub_skill_id=sub_skill_id,
                upstream={**upstream, "characterBible": bible},
            )
            bible = _merge_character_output(bible, sub_skill_id, raw)
            upstream = {**upstream, "characterBible": bible}
            mark_executed(executed, sub_skill_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[CharacterAgent] sub_skill=%s failed", sub_skill_id)
            errors.append(f"{sub_skill_id}: {exc}")

    gate = run_character_gate(bible)
    bible["characterGateLog"] = gate
    mark_executed(executed, "character-gate")
    if not gate.get("passed") and not errors:
        issues = gate.get("issues") or []
        if issues:
            errors.append("; ".join(str(i) for i in issues[:3]))

    try:
        bible = normalize_character_bible_payload(bible, theme=project.theme or "")
        bible = merge_character_ip_lock(bible, brief)
        mark_executed(executed, "ip-character-lock")
        save_artifact(project, "character_bible", bible)
        count = len(bible.get("characters") or []) or sum(
            len(bible.get(k) or []) for k in ("protagonists", "antagonists", "supportingRoles")
        )
        _mark_skill_has_content(project, node_index, f"共 {count} 个角色")
    except Exception as exc:  # noqa: BLE001
        logger.exception("[CharacterAgent] finalize failed")
        errors.append(str(exc))

    persist_execution_trace(project, node_index, AGENT_ID, executed)
    status = "completed" if not errors else "error"
    return AgentResult(
        agent_id=AGENT_ID,
        status=status,
        outputs={"character_bible": bible, "artifact_key": "character_bible"},
        errors=errors,
        meta=agent_execution_meta(AGENT_ID, executed, node_index=node_index),
    )
