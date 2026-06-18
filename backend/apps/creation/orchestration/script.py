# -*- coding: utf-8 -*-
"""ScriptAgent：节点 5 剧本（分批 episode-script-writer + gate + quality guard）。"""
from __future__ import annotations

import logging
from typing import List, Optional

from ..artifact_service import get_artifact, save_artifact
from ..dialogue_shaper import apply_dialogue_shaper
from ..ip_lock import run_script_ip_lock
from ..models import Project
from ..workspace.workspace_editor import _mark_skill_has_content, compute_script_batch_range
from .agent_common import build_standard_upstream, load_project_brief, merge_episodes_by_number
from .agent_detection import run_creator_quality_guard
from .agent_llm import run_sub_skill_llm
from .agent_payload import coerce_script_chunk
from .sub_skill_runner import (
    agent_execution_meta,
    inject_knowledge_upstream,
    mark_executed,
    persist_execution_trace,
)
from .types import AgentResult

logger = logging.getLogger(__name__)

AGENT_ID = "script"
FUSION_NODE_ID = "node-5-script"
NODE_INDEX = 5


def _seed_episode_scripts(project: Project) -> dict:
    existing = get_artifact(project, "episode_scripts") or {}
    if isinstance(existing, dict) and existing:
        return dict(existing)
    return {"nodeId": FUSION_NODE_ID, "projectId": str(project.id), "episodes": []}


def _episode_script_to_markdown(ep: dict) -> str:
    for key in ("scriptMarkdown", "full_script_text", "content"):
        val = (ep.get(key) or "").strip()
        if val:
            return val
    num = ep.get("episodeNumber") or ep.get("episode") or "?"
    title = ep.get("title") or ""
    return f"# 第{num}集：{title}\n\n（待生成）"


def _run_episode_gates(
    project: Project,
    scripts: dict,
    outline: dict,
    *,
    ep_from: int,
    ep_to: int,
) -> dict:
    from apps.creation.validators import validate_episode

    outline_episodes = outline.get("episodes") or []
    gate_logs: List[dict] = []
    passed_all = True
    for ep in scripts.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        num = int(ep.get("episodeNumber") or ep.get("episode") or 0)
        if num < ep_from or num > ep_to:
            continue
        result = validate_episode(ep, outline_episodes=outline_episodes if outline_episodes else None)
        payload = {**result.to_dict(), "episodeNumber": num}
        gate_logs.append(payload)
        if not result.passed:
            passed_all = False
    return {"passed": passed_all, "episodes": gate_logs}


def run_script_agent(
    project: Project,
    *,
    node_index: int = NODE_INDEX,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    **_kwargs,
) -> AgentResult:
    executed: List[str] = []
    errors: List[str] = []

    if script_from is None or script_to is None:
        script_from, script_to, _ = compute_script_batch_range(project)

    ep_from = int(script_from or 1)
    ep_to = int(script_to or ep_from)

    brief = load_project_brief(project)
    structure = get_artifact(project, "structure_plan") or {}
    character_bible = get_artifact(project, "character_bible") or {}
    series_outline = get_artifact(project, "series_outline") or {}
    upstream = build_standard_upstream(
        project,
        brief,
        structure=structure,
        character_bible=character_bible,
        series_outline=series_outline,
    )
    scripts = _seed_episode_scripts(project)

    try:
        upstream = inject_knowledge_upstream(AGENT_ID, upstream, project)
        mark_executed(executed, "reference-injector")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScriptAgent] reference-injector skipped: %s", exc)

    llm_upstream = {
        **upstream,
        "episodeScripts": scripts,
        "episode_scripts": scripts,
        "episodeFrom": ep_from,
        "episodeTo": ep_to,
        "fromEpisode": ep_from,
        "toEpisode": ep_to,
    }

    sub_skill_id = "from-outline-expander" if series_outline.get("episodes") else "episode-script-writer"
    try:
        raw = run_sub_skill_llm(
            project,
            agent_id=AGENT_ID,
            fusion_node_id=FUSION_NODE_ID,
            sub_skill_id=sub_skill_id,
            upstream=llm_upstream,
        )
        chunk = coerce_script_chunk(raw)
        scripts = merge_episodes_by_number(scripts, chunk.get("episodes") or [])
        mark_executed(executed, sub_skill_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("[ScriptAgent] sub_skill=%s failed", sub_skill_id)
        errors.append(f"{sub_skill_id}: {exc}")

    mark_executed(executed, "dialogue-shaper")
    try:
        scripts, _dialogue_log = apply_dialogue_shaper(scripts, character_bible)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScriptAgent] dialogue-shaper skipped: %s", exc)

    try:
        quality = run_creator_quality_guard(scripts)
        scripts["creatorQualityLog"] = quality
        mark_executed(executed, "creator-quality-guard")
        if quality.get("passed") is False and not errors:
            ep_issues = (quality.get("episodes") or [{}])[0].get("issues") or []
            if ep_issues:
                errors.append("; ".join(str(i) for i in ep_issues[:2]))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScriptAgent] creator-quality-guard skipped: %s", exc)

    try:
        gate = _run_episode_gates(
            project,
            scripts,
            series_outline,
            ep_from=ep_from,
            ep_to=ep_to,
        )
        scripts["episodeGateLog"] = gate
        mark_executed(executed, "episode-gate")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScriptAgent] episode-gate skipped: %s", exc)

    try:
        ip_report = run_script_ip_lock(scripts, brief=brief, character_bible=character_bible)
        scripts["ipScriptLockLog"] = ip_report
        mark_executed(executed, "ip-script-lock")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScriptAgent] ip-script-lock skipped: %s", exc)

    try:
        scripts.setdefault("projectId", str(project.id))
        save_artifact(project, "episode_scripts", scripts)
        count = len(scripts.get("episodes") or [])
        _mark_skill_has_content(project, node_index, f"{count} 集剧本")
    except Exception as exc:  # noqa: BLE001
        logger.exception("[ScriptAgent] finalize failed")
        errors.append(str(exc))

    persist_execution_trace(project, node_index, AGENT_ID, executed)
    status = "completed" if not errors else "error"
    return AgentResult(
        agent_id=AGENT_ID,
        status=status,
        outputs={
            "episode_scripts": scripts,
            "artifact_key": "episode_scripts",
            "episode_from": ep_from,
            "episode_to": ep_to,
        },
        errors=errors,
        meta=agent_execution_meta(AGENT_ID, executed, node_index=node_index),
    )
