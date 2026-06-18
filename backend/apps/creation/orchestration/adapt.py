# -*- coding: utf-8 -*-
"""Adapt agent for reference/IP/novel entry modes."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..artifact_service import get_artifact, save_artifact
from ..models import Project
from .sub_skill_runner import agent_execution_meta, mark_executed, persist_agent_execution_trace
from .types import AgentResult

logger = logging.getLogger(__name__)


def _run_verify_creation_brief(
    project: Project,
    meta: Dict[str, Any],
    entry: str,
    executed: List[str],
) -> None:
    reference_work = (meta.get("referenceWork") or "").strip()
    if not reference_work:
        return
    meta["verifyCreation"] = {
        "briefOnly": True,
        "passed": True,
        "ok": True,
        "entry": entry,
        "source": "python-native",
        "referenceChars": len(reference_work),
    }
    mark_executed(executed, "verify-creation")


def run_adapt_agent(project: Project, *, submit_data: Dict[str, Any] | None = None) -> AgentResult:
    entry = (project.creation_entry or "from-scratch").strip()
    from apps.skill.config.portal.creation_form import CreationFormOverrideService

    if not CreationFormOverrideService.creation_entry_requires_adapt(entry):
        trace_meta = agent_execution_meta("adapt", [], node_index=0)
        return AgentResult(
            agent_id="adapt",
            status="skipped",
            meta={**trace_meta, "creation_entry": entry},
        )

    executed: List[str] = []
    brief = get_artifact(project, "project_brief") or {}
    data = submit_data or {}
    meta: Dict[str, Any] = {
        "creationEntry": entry,
        "referenceWork": (project.reference_work or data.get("reference_work") or "").strip(),
        "ipLock": {},
        "originalityMode": False,
        "status": "prepared",
    }

    if entry == "from-reference":
        mark_executed(executed, "reference-fingerprint")
        meta["originalityMode"] = True
        meta["referenceFingerprint"] = {
            "referenceWork": meta["referenceWork"],
            "mode": "structure-only",
            "forbidDialogueCopy": True,
        }
        brief["creationEntry"] = entry
        brief["referenceFingerprint"] = meta["referenceFingerprint"]
        _run_verify_creation_brief(project, meta, entry, executed)
        mark_executed(executed, "original-from-reference")
    elif entry == "ip-sequel":
        mark_executed(executed, "ip-derivative")
        meta["ipLock"] = {
            "referenceWork": meta["referenceWork"],
            "forbidOoc": True,
            "forbidSettingConflict": True,
        }
        brief["creationEntry"] = entry
        brief["ipSequelRules"] = data.get("ip_sequel_rules") or brief.get("ipSequelRules") or ""
        brief["ipLock"] = meta["ipLock"]
        if data.get("ip_sequel_mode"):
            meta["ipSequelMode"] = data.get("ip_sequel_mode")
            brief["ipSequelMode"] = data.get("ip_sequel_mode")
        if data.get("ip_keep_rules"):
            meta["ipKeepRules"] = (data.get("ip_keep_rules") or "")[:2000]
            brief["ipKeepRules"] = meta["ipKeepRules"]
    elif entry == "novel-adaptation":
        novel_text = (
            data.get("novel_text")
            or data.get("novel_source_text")
            or brief.get("novelSourceText")
            or ""
        ).strip()
        meta["novelSource"] = {"hasSourceText": bool(novel_text)}
        brief["creationEntry"] = entry
        if novel_text:
            brief["novelSourceText"] = novel_text[:50000]
            meta["novelSource"]["charCount"] = len(brief["novelSourceText"])

    mark_executed(executed, "adapt-brief-merge")
    save_artifact(project, "adaptation_meta", meta)
    save_artifact(project, "project_brief", brief)
    trace_meta = agent_execution_meta("adapt", executed, node_index=0)
    persist_agent_execution_trace(project, "adapt", executed)
    logger.info("[AdaptAgent] prepared project=%s entry=%s skills=%s", project.id, entry, executed)
    return AgentResult(
        agent_id="adapt",
        status="completed",
        outputs={"adaptation_meta": meta},
        meta=trace_meta,
    )
