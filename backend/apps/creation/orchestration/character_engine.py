# -*- coding: utf-8 -*-
"""CharacterAgent：人物圣经 + 原型匹配 + 关系网（SubSkillOrchestrator）。"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List

from apps.workflow.fusion.schema_validator import validate_against_schema

from ..character_enrichment import normalize_character_bible_payload
from ..ip_lock import merge_character_ip_lock
from .agent_detection import run_character_gate
from .agent_payload import coerce_character_chunk, unwrap_llm_payload
from .knowledge import retrieve_references
from .sub_skill_orchestrator import SubSkillOrchestrator, _deep_merge
from .verify_creation_support import run_reference_verify_if_needed

if TYPE_CHECKING:
    from ..fusion.fusion_orchestrator import FusionOrchestrator

logger = logging.getLogger(__name__)

NODE_ID = "node-3-character"
AGENT_ID = "character"
SCHEMA_FILE = "character-bible.schema.json"


class CharacterAgentEngine:
    def __init__(self, orch: FusionOrchestrator):
        self.orch = orch
        self.project = orch.project
        self.orchestrator = SubSkillOrchestrator(orch, AGENT_ID)
        self.executed_skills: List[str] = []

    def _sync_executed(self) -> None:
        self.executed_skills = self.orchestrator.state.executed_ids()

    def _validate_schema(self, payload: dict) -> None:
        ok, msgs = validate_against_schema(
            payload, f"schemas/{SCHEMA_FILE}", config=self.orch.config
        )
        if not ok and self.orch.strict_schema:
            raise ValueError(f"{NODE_ID} schema 校验失败: {'; '.join(msgs[:5])}")

    def _run_archetype_matcher(self, theme: str) -> dict:
        skill_id = "archetype-matcher"
        orch = self.orchestrator
        try:
            refs = retrieve_references(
                theme=theme,
                tags=["character-archetypes.json", "emotional-archetype-library.json"],
                limit=3,
            )
            blocks = len(refs.get("blocks") or [])
            orch.state.record(
                skill_id,
                "executed",
                skill_type="retrieval",
                message=f"{blocks} 参考块",
            )
            return refs
        except Exception as exc:  # noqa: BLE001
            logger.warning("[CharacterAgent] archetype-matcher failed: %s", exc)
            orch.state.record(skill_id, "failed", skill_type="retrieval", message=str(exc)[:200])
            return {}

    def generate(self, artifacts: Dict[str, Any]) -> dict:
        self.orch._mark_node_running(NODE_ID)
        self.orch._flush_progress(
            node_id=NODE_ID,
            summary="CharacterAgent · 人物体系",
            sub_pct=10,
        )

        orch = self.orchestrator
        brief = artifacts["project_brief"]
        theme = (brief.get("theme") or getattr(self.project, "theme", "") or "").strip()
        archetype_refs = self._run_archetype_matcher(theme)

        upstream = {
            "projectBrief": brief,
            "structurePlan": artifacts["structure_plan"],
            "knowledgeArchetypeRefs": archetype_refs,
        }
        upstream = orch.run_reference_injector(upstream)

        raw_char = orch.run_llm_sub_skill(
            "character-generator",
            NODE_ID,
            upstream,
            token_key=AGENT_ID,
        )
        payload = coerce_character_chunk(raw_char)

        rel_upstream = {
            **upstream,
            "characterBible": payload,
        }
        try:
            rel_patch = orch.run_llm_sub_skill(
                "relationship-weaver",
                NODE_ID,
                rel_upstream,
                token_key=AGENT_ID,
            )
            rel_patch = unwrap_llm_payload("relationship-weaver", rel_patch)
            payload = _deep_merge(payload, rel_patch)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[CharacterAgent] relationship-weaver skipped: %s", exc)
            orch.state.record(
                "relationship-weaver",
                "failed",
                skill_type="llm",
                message=str(exc)[:200],
            )

        payload = normalize_character_bible_payload(
            payload,
            theme=theme,
            archetype_refs=archetype_refs,
        )
        prior = (artifacts.get("character_bible") or {}).get("ipLockRoster")
        payload = merge_character_ip_lock(payload, brief, prior_roster=prior)
        ip_log = payload.get("ipCharacterLockLog") or {}
        if not ip_log.get("skipped"):
            orch.state.record(
                "ip-character-lock",
                "executed" if ip_log.get("passed") else "failed",
                skill_type="rule",
                message=f"锁定 {ip_log.get('lockedCount', 0)} 角色",
            )
        orch.state.record("character-consistency", "executed", skill_type="rule", message="schema 归一化")

        gate = run_character_gate(payload)
        payload["characterGateLog"] = gate
        orch.state.record(
            "character-gate",
            "executed" if gate.get("passed") else "failed",
            skill_type="detection",
            message="; ".join(str(i) for i in (gate.get("issues") or [])[:2])[:200],
        )
        if not gate.get("passed"):
            logger.warning(
                "[CharacterAgent] character-gate issues=%s",
                (gate.get("issues") or [])[:3],
            )

        self._validate_schema(payload)
        run_reference_verify_if_needed(self.orch, artifact="characters", payload=payload)
        self._sync_executed()
        return payload
