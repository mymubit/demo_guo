# -*- coding: utf-8 -*-
"""OutlineAgent：六阶段框架 + 逐集大纲 + sub-plan 校验（SubSkillOrchestrator）。"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from django.conf import settings

from apps.workflow.fusion.schema_registry import FusionSchemaRegistry
from apps.workflow.fusion.schema_validator import validate_against_schema
from apps.skill.llm.chat import LlmServiceError

from ..artifact_service import get_artifact, save_artifact
from ..outline_enrichment import enrich_outline_payload
from ..outline_skeleton import ensure_outline_skeleton, merge_stage_blocks
from ..pipeline_debug_log import log_fusion_node_begin, summarize_artifact
from .agent_payload import coerce_outline_chunk
from .sub_skill_orchestrator import FIXER_MAX_ROUNDS, SubSkillOrchestrator, _deep_merge
from .verify_creation_support import run_reference_verify_if_needed

if TYPE_CHECKING:
    from ..fusion.fusion_orchestrator import FusionOrchestrator

logger = logging.getLogger(__name__)

NODE_ID = "node-4-outline"
AGENT_ID = "outline"


class OutlineAgentEngine:
    def __init__(self, orch: FusionOrchestrator):
        self.orch = orch
        self.project = orch.project
        self.orchestrator = SubSkillOrchestrator(orch, AGENT_ID)
        self.executed_skills: List[str] = []

    def _sync_executed(self) -> None:
        self.executed_skills = self.orchestrator.state.executed_ids()

    def _target_total(self, artifacts: Dict[str, Any]) -> int:
        brief = artifacts.get("project_brief") or {}
        structure = artifacts.get("structure_plan") or {}
        total = int(
            structure.get("totalEpisodes")
            or brief.get("episodeCount")
            or self.project.episode_count
        )
        max_eps_cfg = int(getattr(settings, "FUSION_LLM_MAX_EPISODES", 0))
        if max_eps_cfg > 0:
            return min(total, max_eps_cfg)
        return total

    def _framework_ready(self, outline: dict | None) -> bool:
        from ..outline_skeleton import stage_rough_outline_ready

        if stage_rough_outline_ready(outline or {}):
            return True
        if not isinstance(outline, dict):
            return False
        if outline.get("stageIndex") or outline.get("creativePlan"):
            return True
        rough = (outline.get("roughOutline") or outline.get("structureSummary") or "").strip()
        return len(rough) >= 10

    def _merge_series_outline(
        self,
        existing: dict,
        chunk: dict,
        *,
        first_batch: bool = False,
        allow_empty_episodes: bool = False,
    ) -> dict:
        by_num = {
            int(e["episodeNumber"]): e
            for e in (existing.get("episodes") or [])
            if isinstance(e, dict) and e.get("episodeNumber") is not None
        }
        new_eps = chunk.get("episodes") or []
        if not new_eps and not allow_empty_episodes:
            raise LlmServiceError("LLM 未返回 episodes 数组")
        for ep in new_eps:
            if not isinstance(ep, dict) or ep.get("episodeNumber") is None:
                continue
            by_num[int(ep["episodeNumber"])] = ep

        out = dict(existing) if existing else {}
        meta_keys = (
            "nodeId",
            "nodeName",
            "totalEpisodes",
            "stageIndex",
            "keyHighlights",
            "creativePlan",
            "keyEpisodeIndex",
            "structureSummary",
            "roughOutline",
            "coarseOutline",
        )
        if first_batch or chunk.get("frameworkOnly"):
            for key in meta_keys:
                if chunk.get(key) is not None:
                    out[key] = chunk[key]
            out.setdefault("nodeId", NODE_ID)
            out.setdefault("nodeName", "大纲与创作规划节点")
            out = merge_stage_blocks(out, chunk)
        else:
            for key in ("creativePlan", "keyHighlights", "structureSummary", "roughOutline"):
                if chunk.get(key) and not out.get(key):
                    out[key] = chunk[key]

        out["episodes"] = sorted(by_num.values(), key=lambda x: int(x["episodeNumber"]))
        if not out.get("totalEpisodes"):
            out["totalEpisodes"] = chunk.get("totalEpisodes") or self.project.episode_count
        return out

    def _write_outline_file(self, outline: dict):
        path = self.orch.work_dir / f"{self.project.id.hex}_outline.json"
        path.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _enrich_outline(
        self,
        outline: dict,
        artifacts: Dict[str, Any],
        *,
        total_episodes: Optional[int] = None,
    ) -> dict:
        target = total_episodes if total_episodes is not None else self._target_total(artifacts)
        out = enrich_outline_payload(
            outline,
            structure_plan=artifacts.get("structure_plan") or {},
            character_bible=artifacts.get("character_bible"),
            project_brief=artifacts.get("project_brief"),
            theme=getattr(self.project, "theme", "") or "",
            total_episodes=target,
        )
        self.orchestrator.state.record(
            "conflict-advisor",
            "executed",
            skill_type="rule",
            message="冲突循环 enrichment",
        )
        self.orchestrator.state.record(
            "payment-planner",
            "executed",
            skill_type="rule",
            message="付费卡点 enrichment",
        )
        self.orchestrator.state.record(
            "psychology-advisor",
            "executed",
            skill_type="rule",
            message="心理学策略 enrichment",
        )
        return out

    def _finalize_outline(
        self,
        outline: dict,
        artifacts: Dict[str, Any],
        *,
        strict_validate: bool = True,
    ) -> dict:
        from ..outline_skeleton import expand_legacy_episode_summaries

        structure = artifacts.get("structure_plan") or {}
        target = self._target_total(artifacts)
        outline, _fixed = expand_legacy_episode_summaries(outline)
        outline = self._enrich_outline(outline, artifacts, total_episodes=target)
        outline["totalEpisodes"] = target
        run_reference_verify_if_needed(self.orch, artifact="outline", payload=outline)

        path = self._write_outline_file(outline)
        orch = self.orchestrator
        passed, issues = orch.run_plan_validate(
            path,
            episodes=target,
            strict=strict_validate,
        )
        for _ in range(FIXER_MAX_ROUNDS):
            if passed:
                break
            outline = orch.run_plan_fixer(outline, issues, NODE_ID)
            outline = self._enrich_outline(outline, artifacts, total_episodes=target)
            path = self._write_outline_file(outline)
            passed, issues = orch.run_plan_validate(path, episodes=target, strict=strict_validate)

        if not passed:
            logger.warning("[OutlineAgent] sub-plan 校验未完全通过: %s", issues[:5])

        outline["planValidationLog"] = {
            "passed": passed,
            "issues": list(issues),
            "checker": "sub-plan",
        }

        self._sync_executed()
        return outline

    def generate_framework(
        self,
        artifacts: Dict[str, Any],
        *,
        existing: Optional[dict] = None,
    ) -> dict:
        brief = artifacts["project_brief"]
        structure = artifacts["structure_plan"]
        characters = artifacts["character_bible"]
        target = self._target_total(artifacts)
        orch = self.orchestrator

        self.orch._flush_progress(
            node_id=NODE_ID,
            summary="OutlineAgent · 创作规划 + 六阶段粗纲",
            sub_pct=5,
        )

        upstream = {
            "projectBrief": brief,
            "structurePlan": structure,
            "characterBible": characters,
            "frameworkOnly": True,
            "totalEpisodes": target,
        }
        upstream = orch.run_reference_injector(upstream)

        plan_chunk = orch.run_llm_sub_skill(
            "hook-planner",
            NODE_ID,
            upstream,
            token_key="outline_framework",
        )
        orch.state.record("reversal-scheduler", "executed", skill_type="llm+retrieval", message="并入 hook-planner")
        orch.state.record("psychology-advisor", "executed", skill_type="llm+handbook", message="并入 hook-planner")

        framework_chunk = orch.run_llm_sub_skill(
            "framework-builder",
            NODE_ID,
            {**upstream, "creativePlan": plan_chunk.get("creativePlan"), "stageIndex": plan_chunk.get("stageIndex")},
            token_key="outline_framework",
        )

        chunk = _deep_merge(plan_chunk, framework_chunk)
        chunk["episodes"] = []

        base = dict(existing or {})
        if not base.get("stageBlocks"):
            base = ensure_outline_skeleton(
                self.project,
                persist=False,
                structure_plan=structure,
            )
        if base.get("episodes"):
            chunk["episodes"] = []
        merged = self._merge_series_outline(
            base,
            chunk,
            first_batch=True,
            allow_empty_episodes=True,
        )
        merged["totalEpisodes"] = target
        merged.setdefault("episodes", base.get("episodes") or [])
        merged = self._enrich_outline(merged, artifacts, total_episodes=target)
        self._sync_executed()
        return merged

    def generate_stage_framework(
        self,
        artifacts: Dict[str, Any],
        stage_key: str,
        *,
        existing: Optional[dict] = None,
    ) -> dict:
        brief = artifacts["project_brief"]
        structure = artifacts["structure_plan"]
        characters = artifacts["character_bible"]
        target = self._target_total(artifacts)
        orch = self.orchestrator
        key = str(stage_key or "").strip()
        if not key:
            raise ValueError("未指定阶段")

        outline = dict(existing or {})
        if not outline.get("stageBlocks"):
            outline = ensure_outline_skeleton(
                self.project,
                persist=False,
                structure_plan=structure,
            )

        block = next(
            (b for b in (outline.get("stageBlocks") or []) if isinstance(b, dict) and b.get("key") == key),
            None,
        )
        if not block:
            raise ValueError(f"未找到阶段：{key}")

        label = block.get("label") or key
        self.orch._flush_progress(
            node_id=NODE_ID,
            summary=f"OutlineAgent · {label} 阶段粗纲",
            sub_pct=5,
        )

        upstream_base = {
            "projectBrief": brief,
            "structurePlan": structure,
            "characterBible": characters,
            "frameworkOnly": True,
            "singleStageOnly": True,
            "targetStageKey": key,
            "totalEpisodes": target,
            "existingOutline": {
                "stageBlocks": outline.get("stageBlocks") or [],
                "creativePlan": outline.get("creativePlan"),
                "stageIndex": outline.get("stageIndex"),
                "structureSummary": outline.get("structureSummary") or "",
            },
        }
        upstream_base = orch.run_reference_injector(upstream_base)

        if not outline.get("creativePlan"):
            plan_chunk = orch.run_llm_sub_skill(
                "hook-planner",
                NODE_ID,
                upstream_base,
                token_key="outline_framework",
            )
            orch.state.record(
                "reversal-scheduler",
                "executed",
                skill_type="llm+retrieval",
                message="并入 hook-planner",
            )
            orch.state.record(
                "psychology-advisor",
                "executed",
                skill_type="llm+handbook",
                message="并入 hook-planner",
            )
            outline = self._merge_series_outline(
                outline,
                plan_chunk,
                first_batch=True,
                allow_empty_episodes=True,
            )
            upstream_base = {
                **upstream_base,
                "creativePlan": outline.get("creativePlan"),
                "stageIndex": outline.get("stageIndex"),
                "existingOutline": {
                    **upstream_base["existingOutline"],
                    "creativePlan": outline.get("creativePlan"),
                    "stageIndex": outline.get("stageIndex"),
                },
            }

        framework_chunk = orch.run_llm_sub_skill(
            "framework-builder",
            NODE_ID,
            upstream_base,
            token_key="outline_framework",
        )
        merged = self._merge_series_outline(
            outline,
            framework_chunk,
            first_batch=True,
            allow_empty_episodes=True,
        )
        merged["totalEpisodes"] = target
        merged.setdefault("episodes", outline.get("episodes") or [])
        merged = self._enrich_outline(merged, artifacts, total_episodes=target)
        self._sync_executed()
        return merged

    def generate_episode_range(
        self,
        artifacts: Dict[str, Any],
        from_episode: int,
        to_episode: int,
        *,
        existing: Optional[dict] = None,
    ) -> dict:
        brief = artifacts["project_brief"]
        structure = artifacts["structure_plan"]
        characters = artifacts["character_bible"]
        target = self._target_total(artifacts)
        start = max(1, int(from_episode))
        end = min(max(start, int(to_episode)), target)
        orch = self.orchestrator

        outline = dict(existing or artifacts.get("series_outline") or {})
        if not self._framework_ready(outline):
            outline = self.generate_framework(artifacts, existing=outline)
            if not self.orch.dry_run:
                save_artifact(self.project, "series_outline", outline)

        for ep_num in range(start, end + 1):
            self.orch._flush_progress(
                node_id=NODE_ID,
                summary=f"OutlineAgent · 第 {ep_num} 集大纲 / 共 {target} 集",
                sub_pct=int((ep_num - 1) / max(target, 1) * 100),
            )
            existing_eps = outline.get("episodes") or []
            context_eps = [
                e
                for e in existing_eps
                if isinstance(e, dict) and int(e.get("episodeNumber", 0)) < ep_num
            ][-3:]
            upstream = {
                "projectBrief": brief,
                "structurePlan": structure,
                "characterBible": characters,
                "generateFromEpisode": ep_num,
                "generateToEpisode": ep_num,
                "includeOutlineMeta": False,
                "frameworkOnly": False,
                "totalEpisodes": target,
                "existingOutline": {
                    "stageBlocks": outline.get("stageBlocks") or [],
                    "roughOutline": outline.get("roughOutline") or outline.get("structureSummary"),
                    "stageIndex": outline.get("stageIndex"),
                    "creativePlan": outline.get("creativePlan"),
                    "recentEpisodes": context_eps,
                },
            }
            upstream = inject_knowledge_once(orch, upstream)
            chunk = orch.run_llm_sub_skill(
                "episode-outline-writer",
                NODE_ID,
                upstream,
                token_key="outline_episode",
            )
            chunk = coerce_outline_chunk(chunk)
            if not (chunk.get("episodes") or []):
                chunk = coerce_outline_chunk(
                    orch.run_llm_sub_skill(
                        "episode-outline-writer",
                        NODE_ID,
                        upstream,
                        token_key="outline_episode",
                    )
                )
            outline = self._merge_series_outline(outline, chunk, first_batch=False)
            if not self.orch.dry_run:
                save_artifact(self.project, "series_outline", outline)

        outline["totalEpisodes"] = target
        return self._finalize_outline(outline, artifacts)

    def generate_auto(self, artifacts: Dict[str, Any]) -> dict:
        self.orch._require_llm(NODE_ID)
        self.orch._mark_node_running(NODE_ID)

        target = self._target_total(artifacts)
        existing = dict(artifacts.get("series_outline") or {})

        from apps.workflow.step_admin import PipelineStepAdminService

        provider_id = PipelineStepAdminService.resolve_provider_id(NODE_ID)
        log_fusion_node_begin(
            project_id=self.project.id,
            node_id=NODE_ID,
            node_index=self.orch._node_index(NODE_ID),
            upstream={
                "agentId": AGENT_ID,
                "mode": "auto",
                "totalEpisodes": target,
                "frameworkReady": self._framework_ready(existing),
            },
            prompt_stats={"providerId": provider_id},
        )

        if not self._framework_ready(existing):
            existing = self.generate_framework(artifacts, existing=existing)
            if not self.orch.dry_run:
                save_artifact(self.project, "series_outline", existing)

        filled = {
            int(e.get("episodeNumber"))
            for e in (existing.get("episodes") or [])
            if isinstance(e, dict) and e.get("episodeNumber") is not None
        }
        missing = [n for n in range(1, target + 1) if n not in filled]
        for ep_num in missing:
            existing = self.generate_episode_range(
                artifacts,
                ep_num,
                ep_num,
                existing=existing,
            )

        if len(existing.get("episodes") or []) < target:
            raise LlmServiceError(
                f"OutlineAgent 仅生成 {len(existing.get('episodes') or [])}/{target} 集大纲"
            )

        existing["totalEpisodes"] = target
        schema_reg = FusionSchemaRegistry(self.orch.config)
        schema_file = schema_reg.schema_file_for_artifact("series_outline") or "series-outline.schema.json"
        ok, msgs = validate_against_schema(existing, schema_file, config=self.orch.config)
        if not ok:
            logger.warning(
                "OutlineAgent schema 警告: %s output=%s",
                msgs[:5],
                summarize_artifact("series_outline", existing),
            )
            if self.orch.strict_schema:
                raise ValueError(f"node-4-outline schema 校验失败: {'; '.join(msgs[:5])}")
        return self._finalize_outline(existing, artifacts)

    def run_workspace(
        self,
        artifacts: Dict[str, Any],
        *,
        framework_only: bool = False,
        stage_key: Optional[str] = None,
        from_episode: Optional[int] = None,
        to_episode: Optional[int] = None,
        existing: Optional[dict] = None,
    ) -> dict:
        self.orch._require_llm(NODE_ID)
        self.orch._mark_node_running(NODE_ID)

        if existing is None:
            existing = get_artifact(self.project, "series_outline") or {}

        if stage_key:
            outline = self.generate_stage_framework(
                artifacts,
                stage_key,
                existing=existing if isinstance(existing, dict) else {},
            )
            return self._enrich_outline(
                outline,
                artifacts,
                total_episodes=self._target_total(artifacts),
            )

        if framework_only:
            outline = self.generate_framework(
                artifacts,
                existing=existing if isinstance(existing, dict) else {},
            )
            return self._enrich_outline(
                outline,
                artifacts,
                total_episodes=self._target_total(artifacts),
            )

        if from_episode is not None and to_episode is not None:
            return self.generate_episode_range(
                artifacts,
                from_episode,
                to_episode,
                existing=existing if isinstance(existing, dict) else {},
            )

        return self.generate_auto(artifacts)


def inject_knowledge_once(orch: SubSkillOrchestrator, upstream: Dict[str, Any]) -> Dict[str, Any]:
    if upstream.get("knowledgeReferences"):
        return upstream
    return orch.run_reference_injector(upstream)
