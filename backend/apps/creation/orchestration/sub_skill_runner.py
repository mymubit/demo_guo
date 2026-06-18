# -*- coding: utf-8 -*-
"""Sub-skill trace helpers for the ScriptForge runtime."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from django.utils import timezone

from apps.agent.runtime import get_agent

from ..artifact_service import get_artifact, save_artifact
from ..models import Project

TRACE_ARTIFACT_KEY = "agent_execution_traces"


def reference_files_for_agent(agent_id: str) -> List[str]:
    agent = get_agent(agent_id) or {}
    files: List[str] = []
    for skill in agent.get("sub_skills") or []:
        if not isinstance(skill, dict):
            continue
        for ref in skill.get("references") or []:
            if isinstance(ref, str) and ref not in files:
                files.append(ref)
    return files


def inject_knowledge_upstream(agent_id: str, upstream: Dict[str, Any], project: Project) -> Dict[str, Any]:
    from .knowledge import retrieve_references

    out = dict(upstream)
    refs = reference_files_for_agent(agent_id)
    out["knowledgeReferences"] = retrieve_references(
        theme=(project.theme or "").strip(),
        tags=refs[:5] if refs else None,
    )
    return out


def mark_executed(executed: List[str], skill_id: str) -> None:
    if skill_id and skill_id not in executed:
        executed.append(skill_id)


def sub_skill_meta(agent_id: str, skill_id: str) -> Optional[Dict[str, Any]]:
    agent = get_agent(agent_id) or {}
    for skill in agent.get("sub_skills") or []:
        if isinstance(skill, dict) and skill.get("id") == skill_id:
            return skill
    return None


def build_execution_trace(
    agent_id: str,
    executed: List[str],
    *,
    trace_entries: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, str]]:
    if trace_entries:
        return list(trace_entries)
    agent = get_agent(agent_id) or {}
    defined = {s.get("id"): s for s in (agent.get("sub_skills") or []) if isinstance(s, dict)}
    trace: List[Dict[str, str]] = []
    for skill_id in executed:
        meta = defined.get(skill_id) or {}
        trace.append(
            {
                "id": skill_id,
                "type": str(meta.get("type") or ""),
                "cli": "",
                "script": "",
                "status": "executed",
                "message": "",
            }
        )
    for skill_id, meta in defined.items():
        if skill_id not in executed:
            trace.append(
                {
                    "id": skill_id,
                    "type": str(meta.get("type") or ""),
                    "cli": "",
                    "script": "",
                    "status": "skipped",
                    "message": "",
                }
            )
    return trace


def agent_execution_meta(
    agent_id: str,
    executed: List[str],
    *,
    node_index: int,
    trace_entries: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    agent_def = get_agent(agent_id) or {}
    return {
        "node_index": node_index,
        "sub_skills": [
            {
                "id": str(s.get("id") or ""),
                "type": str(s.get("type") or ""),
                "cli": "",
            }
            for s in (agent_def.get("sub_skills") or [])
            if isinstance(s, dict)
        ],
        "executed_sub_skills": list(executed),
        "execution_trace": build_execution_trace(agent_id, executed, trace_entries=trace_entries),
        "output_artifacts": agent_def.get("outputs") or [],
    }


def _get_rule_version_snapshot() -> Dict[str, str]:
    try:
        from apps.skill.skills.loader import get_skill_rule_loader

        loader = get_skill_rule_loader()
        snapshot: Dict[str, str] = {}
        for tier_name, getter in [
            ("tier1", loader.get_tier1),
            ("tier2", loader.get_tier2),
            ("tier3", loader.get_tier3),
            ("tier4", loader.get_tier4),
        ]:
            try:
                raw = getter()
            except Exception:  # noqa: BLE001
                raw = {}
            if isinstance(raw, dict):
                snapshot[tier_name] = str(raw.get("version") or raw.get("_version") or "")
        return snapshot
    except Exception:  # noqa: BLE001
        return {}


def persist_agent_execution_trace(project: Project, agent_id: str, executed: List[str]) -> None:
    store = dict(get_artifact(project, TRACE_ARTIFACT_KEY) or {})
    store[agent_id] = {
        "agentId": agent_id,
        "executedSubSkills": list(executed),
        "skillRuleVersions": _get_rule_version_snapshot(),
        "updatedAt": timezone.now().isoformat(),
    }
    save_artifact(project, TRACE_ARTIFACT_KEY, store)


def persist_execution_trace(
    project: Project,
    node_index: int,
    agent_id: str,
    executed: List[str],
    *,
    trace_entries: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    trace = agent_execution_meta(
        agent_id,
        executed,
        node_index=int(node_index),
        trace_entries=trace_entries,
    )
    store = dict(get_artifact(project, TRACE_ARTIFACT_KEY) or {})
    store[agent_id] = {
        "agentId": agent_id,
        "nodeIndex": int(node_index),
        "executedSubSkills": list(executed),
        "executionTrace": trace.get("execution_trace") or [],
        "skillRuleVersions": _get_rule_version_snapshot(),
        "updatedAt": timezone.now().isoformat(),
    }
    save_artifact(project, TRACE_ARTIFACT_KEY, store)
    return store[agent_id]


def latest_agent_execution_trace(project: Project, agent_id: str) -> Dict[str, Any]:
    store = get_artifact(project, TRACE_ARTIFACT_KEY) or {}
    return store.get(agent_id) or {}


def _removed_cli(*args, **kwargs) -> Dict[str, Any]:
    raise RuntimeError("External CLI sub-skills have been removed; use Python services or SkillInvoker.")


def run_cli_sub_skill(*args, **kwargs) -> Dict[str, Any]:
    return _removed_cli(*args, **kwargs)


def resolve_registry_script_path(*args, **kwargs) -> Path:
    _removed_cli(*args, **kwargs)
    raise AssertionError("unreachable")


def unwrap_fusion_cli_result(result: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(result, dict):
        return result.get("json") if isinstance(result.get("json"), dict) else result
    return {}


def _cli_path(path: Union[str, Path]) -> str:
    return str(Path(path).resolve())


cli_verify_creation_brief = _removed_cli
cli_verify_creation_setting = _removed_cli
cli_brief_enrich = _removed_cli
cli_world_validate = _removed_cli
cli_plan_validate = _removed_cli
cli_episode_gate = _removed_cli
cli_gate_full = _removed_cli
cli_compliance_check = _removed_cli
cli_score_deep = _removed_cli
cli_score_quick = _removed_cli
cli_marketing_kit = _removed_cli
cli_pipeline_writeback = _removed_cli
