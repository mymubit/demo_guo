# -*- coding: utf-8 -*-
"""WorldAgent：节点 2 结构与世界观（registry sub_skills 编排）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..artifact_service import get_artifact, save_artifact
from ..display.structure_display import (
    build_world_validation_log,
    enrich_structure_payload,
    normalize_structure_payload,
)
from ..models import Project
from ..schema_mappers import build_project_brief
from ..workspace.workspace_content import ensure_brief_seed_enriched
from ..workspace.workspace_editor import _mark_skill_has_content
from .agent_llm import run_sub_skill_llm
from .agent_payload import extract_fixer_patch, fixer_patch_meaningful, unwrap_llm_payload
from .sub_skill_runner import (
    agent_execution_meta,
    inject_knowledge_upstream,
    mark_executed,
    persist_execution_trace,
)
from .types import AgentResult

logger = logging.getLogger(__name__)

AGENT_ID = "world"
FUSION_NODE_ID = "node-2-structure"
NODE_INDEX = 2

_LLM_SUB_SKILLS = (
    "structure-generator",
    "world-builder",
    "dream-indicators",
)


def _deep_merge(base: dict, patch: dict) -> dict:
    out = dict(base)
    for key, val in patch.items():
        if val is None:
            continue
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def _build_upstream(project: Project, brief: dict) -> Dict[str, Any]:
    return {
        "projectBrief": brief,
        "theme": project.theme or brief.get("theme") or "",
        "episodeCount": project.episode_count or brief.get("episodeCount"),
    }


def _seed_structure_plan(project: Project, brief: dict) -> dict:
    return {
        "nodeId": FUSION_NODE_ID,
        "projectId": str(project.id),
        "workingTitle": brief.get("workingTitle") or project.title or "",
        "totalEpisodes": int(project.episode_count or brief.get("episodeCount") or 80),
        "formatVariant": brief.get("formatVariant") or "",
    }


def _merge_sub_skill_output(plan: dict, sub_skill_id: str, raw: Any) -> dict:
    chunk = unwrap_llm_payload(sub_skill_id, raw)
    if not chunk:
        return plan
    if sub_skill_id == "world-builder" and isinstance(chunk.get("worldview"), dict):
        wv = dict(plan.get("worldview") or {})
        plan["worldview"] = _deep_merge(wv, chunk["worldview"])
        for key, val in chunk.items():
            if key != "worldview" and val is not None:
                plan[key] = val
        return plan
    if sub_skill_id == "dream-indicators":
        wv = dict(plan.get("worldview") or {})
        indicators = chunk.get("dreamIndicators") or chunk.get("dream_indicators")
        if isinstance(indicators, dict):
            wv["dreamIndicators"] = indicators
        plan["worldview"] = wv
        return plan
    return _deep_merge(plan, chunk)


def _run_world_validator(project: Project, plan: dict) -> dict:
    from apps.creation.validators import validate_world

    result = validate_world(plan)
    return result.to_dict()


def _finalize_structure_plan(project: Project, plan: dict) -> dict:
    brief = get_artifact(project, "project_brief") or build_project_brief(project)
    plan.setdefault("projectId", str(project.id))
    plan.setdefault("nodeId", FUSION_NODE_ID)
    plan.setdefault("totalEpisodes", int(project.episode_count or brief.get("episodeCount") or 80))
    plan = enrich_structure_payload(
        plan,
        theme=project.theme or "",
        episode_count=plan.get("totalEpisodes"),
    )
    plan = normalize_structure_payload(plan, project)
    save_artifact(project, "structure_plan", plan)
    _mark_skill_has_content(
        project,
        NODE_INDEX,
        f"{plan.get('totalEpisodes', project.episode_count)}集结构规划",
    )
    return plan


def run_world_agent(project: Project, *, node_index: int = NODE_INDEX, **_kwargs) -> AgentResult:
    """执行 world Agent：reference-injector → LLM 子技能 → sub-world 校验 →（可选）world-fixer。"""
    executed: List[str] = []
    errors: List[str] = []

    ensure_brief_seed_enriched(project)
    brief = get_artifact(project, "project_brief") or build_project_brief(project)
    upstream = _build_upstream(project, brief)
    plan = _seed_structure_plan(project, brief)

    try:
        upstream = inject_knowledge_upstream(AGENT_ID, upstream, project)
        mark_executed(executed, "reference-injector")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[WorldAgent] reference-injector skipped: %s", exc)

    for sub_skill_id in _LLM_SUB_SKILLS:
        try:
            raw = run_sub_skill_llm(
                project,
                agent_id=AGENT_ID,
                fusion_node_id=FUSION_NODE_ID,
                sub_skill_id=sub_skill_id,
                upstream={**upstream, "structurePlan": plan},
            )
            plan = _merge_sub_skill_output(plan, sub_skill_id, raw)
            upstream = {**upstream, "structurePlan": plan}
            mark_executed(executed, sub_skill_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[WorldAgent] sub_skill=%s failed", sub_skill_id)
            errors.append(f"{sub_skill_id}: {exc}")

    validation: dict = {}
    try:
        plan = enrich_structure_payload(
            plan,
            theme=project.theme or "",
            episode_count=plan.get("totalEpisodes"),
        )
        validation = _run_world_validator(project, plan)
        mark_executed(executed, "world-validator")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[WorldAgent] world-validator skipped: %s", exc)
        validation = build_world_validation_log(plan)

    if not validation.get("passed"):
        issues = list(validation.get("issues") or [])
        try:
            fixer_upstream = {
                **upstream,
                "structurePlan": plan,
                "validationIssues": issues,
            }
            fix_raw = run_sub_skill_llm(
                project,
                agent_id=AGENT_ID,
                fusion_node_id=FUSION_NODE_ID,
                sub_skill_id="world-fixer",
                upstream=fixer_upstream,
                system_hint=(
                    "你是世界观修复编辑。根据 validationIssues 修复 structurePlan，"
                    "输出完整 structurePlan JSON（含 worldview.rootRules ≥2 条）。"
                ),
            )
            patch = extract_fixer_patch("world-fixer", fix_raw)
            if fixer_patch_meaningful(patch):
                plan = _deep_merge(plan, patch)
                mark_executed(executed, "world-fixer")
                validation = _run_world_validator(project, plan)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[WorldAgent] world-fixer skipped: %s", exc)

    plan["worldValidationLog"] = {
        "passed": bool(validation.get("passed")),
        "issues": list(validation.get("issues") or []),
        "checker": "sub-world",
    }

    if not validation.get("passed") and not errors:
        issues = validation.get("issues") or []
        if issues:
            errors.append("; ".join(str(i) for i in issues[:3]))

    try:
        plan = _finalize_structure_plan(project, plan)
    except Exception as exc:  # noqa: BLE001
        logger.exception("[WorldAgent] finalize failed")
        errors.append(str(exc))

    persist_execution_trace(
        project,
        node_index,
        AGENT_ID,
        executed,
    )

    status = "completed" if not errors else "error"
    meta = agent_execution_meta(AGENT_ID, executed, node_index=node_index)
    return AgentResult(
        agent_id=AGENT_ID,
        status=status,
        outputs={"structure_plan": plan, "artifact_key": "structure_plan"},
        errors=errors,
        meta=meta,
    )
