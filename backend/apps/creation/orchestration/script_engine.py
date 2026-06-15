# -*- coding: utf-8 -*-
"""ScriptAgent：逐集剧本 + 逐集 gate（SubSkillOrchestrator，小批量 gate）。"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from django.conf import settings

from apps.workflow.fusion.schema_registry import FusionSchemaRegistry
from apps.workflow.fusion.schema_validator import validate_against_schema
from apps.skill.llm.chat import LlmServiceError

from ..artifact_service import get_artifact
from ..dialogue_shaper import apply_dialogue_shaper
from ..episode_gate import apply_episode_gates
from ..ip_lock import run_script_ip_lock
from ..script_psychology import build_episode_psychology_hints
from .agent_detection import run_creator_quality_guard
from .agent_payload import coerce_script_chunk
from .sub_skill_orchestrator import SubSkillOrchestrator
from .verify_creation_support import run_script_originality_gate

if TYPE_CHECKING:
    from ..fusion.fusion_orchestrator import FusionOrchestrator

logger = logging.getLogger(__name__)

NODE_ID = "node-5-script"
AGENT_ID = "script"
DEFAULT_BATCH_SIZE = 2


class ScriptAgentEngine:
    def __init__(self, orch: FusionOrchestrator):
        self.orch = orch
        self.project = orch.project
        self.orchestrator = SubSkillOrchestrator(orch, AGENT_ID)
        self.executed_skills: List[str] = []

    def _sync_executed(self) -> None:
        self.executed_skills = self.orchestrator.state.executed_ids()

    def _batch_size(self) -> int:
        raw = int(getattr(settings, "FUSION_LLM_EPISODE_BATCH", DEFAULT_BATCH_SIZE) or DEFAULT_BATCH_SIZE)
        return max(1, min(raw, 5))

    def _character_id_map(self, characters: dict) -> dict:
        mapping: Dict[str, str] = {}
        for role_list in ("protagonists", "antagonists", "supportingRoles"):
            for c in characters.get(role_list) or []:
                if c.get("id") and c.get("name"):
                    mapping[c["id"]] = c["name"]
        for c in characters.get("characters") or []:
            if isinstance(c, dict) and c.get("id") and c.get("name"):
                mapping[c["id"]] = c["name"]
        return mapping

    def _coerce_episode_chunk(self, chunk: Any) -> dict:
        return coerce_script_chunk(chunk)

    def _llm_script_batch_with_retry(
        self,
        *,
        brief: dict,
        outline: dict,
        characters: dict,
        start: int,
        end: int,
    ) -> dict:
        chunk = self._llm_script_batch(
            brief=brief,
            outline=outline,
            characters=characters,
            start=start,
            end=end,
        )
        chunk = self._coerce_episode_chunk(chunk)
        if not (chunk.get("episodes") or []):
            chunk = self._coerce_episode_chunk(
                self._llm_script_batch(
                    brief=brief,
                    outline=outline,
                    characters=characters,
                    start=start,
                    end=end,
                )
            )
        return chunk

    def _merge_episode_scripts(
        self,
        existing: dict,
        chunk: dict,
        brief: dict,
        characters: dict,
    ) -> dict:
        by_num = {e["episodeNumber"]: e for e in (existing.get("episodes") or [])}
        new_eps = chunk.get("episodes") or []
        if not new_eps:
            raise LlmServiceError("LLM 未返回 episodes 数组")
        for ep in new_eps:
            by_num[ep["episodeNumber"]] = ep
        char_map = chunk.get("characterIdToNameMap") or self._character_id_map(characters)
        return {
            "nodeId": NODE_ID,
            "nodeName": chunk.get("nodeName") or "剧本创作节点",
            "formatVariant": chunk.get("formatVariant") or brief.get("formatVariant", "variant-b"),
            "characterIdToNameMap": char_map,
            "episodes": sorted(by_num.values(), key=lambda x: x["episodeNumber"]),
        }

    def _llm_script_batch(
        self,
        *,
        brief: dict,
        outline: dict,
        characters: dict,
        start: int,
        end: int,
    ) -> dict:
        orch = self.orchestrator
        upstream = orch.run_reference_injector(
            {
                "projectBrief": brief,
                "characterBible": characters,
                "seriesOutline": outline,
                "generateFromEpisode": start,
                "generateToEpisode": end,
                "psychologyHints": build_episode_psychology_hints(
                    outline,
                    from_episode=start,
                    to_episode=end,
                ),
            }
        )
        orch.state.record(
            "psychology-advisor",
            "executed",
            skill_type="rule",
            message=f"第{start}-{end}集心理提示",
        )
        chunk = orch.run_llm_sub_skill(
            "episode-script-writer",
            NODE_ID,
            upstream,
            token_key="script_batch",
        )
        orch.state.record(
            "from-outline-expander",
            "executed",
            skill_type="llm",
            message=f"第{start}-{end}集",
        )
        return chunk

    def _apply_gates(
        self,
        episodes: List[dict],
        outline: dict,
        *,
        filter_nums: Optional[set] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> List[dict]:
        if not getattr(settings, "FUSION_EPISODE_GATE_ENABLED", True):
            self.orchestrator.state.record("episode-gate", "skipped", skill_type="cli", message="已禁用")
            return episodes

        to_gate = episodes
        if filter_nums is not None:
            to_gate = [e for e in episodes if e.get("episodeNumber") in filter_nums]

        def _on_gate(done: int, ep_num: int) -> None:
            if on_progress:
                on_progress(done, ep_num)

        gated = apply_episode_gates(
            to_gate,
            outline,
            work_dir=self.orch.work_dir,
            project_hex=self.project.id.hex,
            runner=self.orch.runner,
            strict=False,
            on_progress=_on_gate,
        )
        self.orchestrator.state.record("episode-gate", "executed", skill_type="cli")
        self.orchestrator.state.record("script-formatter-lite", "executed", skill_type="cli")

        if filter_nums is None:
            return gated

        by_num = {e["episodeNumber"]: e for e in episodes}
        for ep in gated:
            by_num[ep["episodeNumber"]] = ep
        return sorted(by_num.values(), key=lambda x: x["episodeNumber"])

    def _apply_dialogue_shaper(self, merged: dict, characters: dict) -> dict:
        shaped, log = apply_dialogue_shaper(merged, characters)
        status = "executed" if not log.get("skipped") else "skipped"
        msg = ""
        if log.get("truncatedCount"):
            msg = f"截断 {log['truncatedCount']} 条"
        self.orchestrator.state.record("dialogue-shaper", status, skill_type="rule", message=msg)
        shaped["dialogueShaperLog"] = log
        return shaped

    def _apply_adapt_constraints(self, payload: dict, brief: dict, characters: dict) -> dict:
        report = run_script_ip_lock(payload, brief=brief, character_bible=characters)
        if not report.get("skipped"):
            payload["ipScriptLockLog"] = report
            self.orchestrator.state.record(
                "ip-script-lock",
                "executed" if report.get("passed") else "failed",
                skill_type="rule",
                message="; ".join(str(i) for i in (report.get("issues") or [])[:2])[:200],
            )
        return payload

    def _finalize_payload(self, merged: dict, brief: dict, characters: Optional[dict] = None) -> dict:
        payload = {
            "nodeId": NODE_ID,
            "nodeName": "剧本创作节点",
            "formatVariant": brief.get("formatVariant", "variant-b"),
            "characterIdToNameMap": merged.get("characterIdToNameMap") or {},
            "episodes": merged.get("episodes") or [],
        }
        schema_reg = FusionSchemaRegistry(self.orch.config)
        schema_file = schema_reg.schema_file_for_artifact("episode_scripts") or "episode-scripts.schema.json"
        ok, msgs = validate_against_schema(payload, schema_file, config=self.orch.config)
        if not ok and self.orch.strict_schema:
            raise ValueError(f"episode_scripts schema: {'; '.join(msgs[:5])}")
        payload = self._apply_adapt_constraints(payload, brief, characters or {})
        quality = run_creator_quality_guard(payload)
        payload["creatorQualityGuardLog"] = quality
        self.orchestrator.state.record(
            "creator-quality-guard",
            "executed" if quality.get("passed") or quality.get("skipped") else "failed",
            skill_type="detection",
            message="; ".join(str(i) for i in (quality.get("issues") or [])[:2])[:200],
        )
        if not quality.get("passed") and not quality.get("skipped"):
            logger.warning(
                "[ScriptAgent] creator-quality-guard issues=%s",
                (quality.get("issues") or [])[:3],
            )
        if run_script_originality_gate(self.orch, payload) is not None:
            self.orchestrator.state.record("originality-gate", "executed", skill_type="detection")
        self._sync_executed()
        return payload

    def generate_auto(self, artifacts: Dict[str, Any]) -> dict:
        self.orch._require_llm(NODE_ID)
        self.orch._mark_node_running(NODE_ID)

        brief = artifacts["project_brief"]
        outline = artifacts["series_outline"]
        characters = artifacts["character_bible"]
        total = int(outline.get("totalEpisodes") or self.project.episode_count)
        batch = self._batch_size()
        max_eps_cfg = int(getattr(settings, "FUSION_LLM_MAX_EPISODES", 0))
        target = total if max_eps_cfg <= 0 else min(total, max_eps_cfg)

        existing: dict = {"episodes": []}
        start = 1
        while start <= target:
            end = min(start + batch - 1, target)
            self.orch._flush_progress(
                node_id=NODE_ID,
                summary=f"ScriptAgent · 第{start}-{end}集 / 共{target}集",
                sub_pct=int((start - 1) / max(target, 1) * 100),
            )
            chunk = self._llm_script_batch_with_retry(
                brief=brief,
                outline=outline,
                characters=characters,
                start=start,
                end=end,
            )
            existing = self._merge_episode_scripts(existing, chunk, brief, characters)
            existing = self._apply_dialogue_shaper(existing, characters)
            new_nums = set(range(start, end + 1))
            episodes = self._apply_gates(
                list(existing.get("episodes") or []),
                outline,
                filter_nums=new_nums,
                on_progress=lambda done, ep_num: self.orch._flush_progress(
                    node_id=NODE_ID,
                    summary=f"逐集质检 {done}/{len(new_nums)}（第{ep_num}集）",
                    sub_pct=int((start - 1 + done) / max(target, 1) * 100),
                ),
            )
            existing["episodes"] = episodes
            written = len(existing["episodes"])
            self.orch._flush_progress(
                node_id=NODE_ID,
                summary=f"已生成并质检 {written}/{target} 集剧本",
                sub_pct=int(written / max(target, 1) * 100),
            )
            start = end + 1

        if len(existing.get("episodes") or []) < target:
            raise LlmServiceError(
                f"ScriptAgent 仅生成 {len(existing['episodes'])}/{target} 集"
            )

        return self._finalize_payload(existing, brief, characters)

    def generate_episode_range(
        self,
        artifacts: Dict[str, Any],
        from_episode: int,
        to_episode: int,
        *,
        existing: Optional[dict] = None,
    ) -> dict:
        self.orch._require_llm(NODE_ID)
        self.orch._mark_node_running(NODE_ID)

        brief = artifacts["project_brief"]
        outline = artifacts["series_outline"]
        characters = artifacts["character_bible"]
        start = max(1, int(from_episode))
        end = max(start, int(to_episode))

        if existing is None:
            existing = get_artifact(self.project, "episode_scripts") or {"episodes": []}
        if not isinstance(existing, dict):
            existing = {"episodes": []}

        self.orch._flush_progress(
            node_id=NODE_ID,
            summary=f"ScriptAgent · 第{start}-{end}集",
            sub_pct=10,
        )
        chunk = self._llm_script_batch_with_retry(
            brief=brief,
            outline=outline,
            characters=characters,
            start=start,
            end=end,
        )
        merged = self._merge_episode_scripts(existing, chunk, brief, characters)
        merged = self._apply_dialogue_shaper(merged, characters)
        new_nums = set(range(start, end + 1))
        episodes = self._apply_gates(
            list(merged.get("episodes") or []),
            outline,
            filter_nums=new_nums,
            on_progress=lambda done, ep_num: self.orch._flush_progress(
                node_id=NODE_ID,
                summary=f"逐集质检 {done}/{len(new_nums)}（第{ep_num}集）",
                sub_pct=int(done / max(len(new_nums), 1) * 100),
            ),
        )
        merged["episodes"] = episodes
        return self._finalize_payload(merged, brief, characters)

    def run_workspace(
        self,
        artifacts: Dict[str, Any],
        *,
        from_episode: Optional[int] = None,
        to_episode: Optional[int] = None,
        existing: Optional[dict] = None,
    ) -> dict:
        if from_episode is not None and to_episode is not None:
            return self.generate_episode_range(
                artifacts,
                from_episode,
                to_episode,
                existing=existing,
            )
        return self.generate_auto(artifacts)
