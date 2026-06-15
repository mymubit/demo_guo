# -*- coding: utf-8 -*-
"""按 registry sub_skill 类型真实编排执行，并记录诚实轨迹。"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from apps.workflow.fusion.schema_validator import validate_against_schema
from apps.skill.llm.chat import LlmService, LlmServiceError

from ..display.structure_display import enrich_structure_payload, normalize_structure_payload
from .agent_payload import extract_fixer_patch, fixer_patch_meaningful, unwrap_llm_payload
from .llm_tokens import resolve_agent_max_tokens
from .sub_skill_runner import (
    cli_brief_enrich,
    cli_plan_validate,
    cli_world_validate,
    inject_knowledge_upstream,
    sub_skill_meta,
    unwrap_fusion_cli_result,
)

if TYPE_CHECKING:
    from ..fusion.fusion_orchestrator import FusionOrchestrator

logger = logging.getLogger(__name__)

FIXER_MAX_ROUNDS = 2

_SUB_SKILL_SYSTEM_HINTS: Dict[str, str] = {
    "structure-generator": (
        "你是短剧结构策划师。根据 projectBrief 与 knowledgeReferences（含 hook-types-library、"
        "reversal-patterns-library）生成结构规划 JSON 片段。"
        "必须包含：nodeId=node-2-structure、workingTitle、totalEpisodes、formatVariant、"
        "sixStagePlan 恰好 6 项（每项 coreTask≥30 字）、rhythmCurve 按每 10 集一段覆盖全剧"
        "（每段含 intensityLevel、keyEvents、notes，并附 suggestedHookCodes 2-3 个，"
        "代码须来自 hook-types-library，如 HOOK-SLAP-01）、"
        "keyReversalPoints 至少 8 个（每项必填 reversalCode，对照 reversal-patterns-library，"
        "如 REV-ID-01；含 reversalType、description、foreshadowEpisodes）、"
        "coreStoryArc 五段各≥30 字、structuralConstraints 全字段。"
        "worldview 可先留空对象。只输出 JSON。"
    ),
    "world-builder": (
        "你是短剧世界观策划师（对齐 world-setting-builder）。根据 projectBrief、既有 structurePlan"
        "与 knowledgeReferences，生成完整 worldview 块："
        "settingSummary≥80 字（造梦师全景地图式概述）、timePeriod、locationType、"
        "rootRules≥3 条（首条为第一铁律，一句话说清）、"
        "coreNouns 3-7 个（每项含 term/definition/tier，tier 取 root|mechanism|trace|carrier|derived）、"
        "subWorldConsistency（businessLogic/designProfession/socialHierarchy/economicLogic 各≥20 字）、"
        "dreamIndicators（absoluteSafety/efficientSatisfaction/enhancedRealism 各 6-10 与 notes≥30 字）。"
        "输出 JSON：{\"worldview\": {...}}，可含对 workingTitle 的微调。只输出 JSON。"
    ),
    "world-fixer": (
        "你是结构与世界观修复编辑。根据 sub-world 校验 issues 修复 structure-plan JSON。"
        "保留已有合理内容，仅修正违规字段；不得删除 keyReversalPoints.reversalCode、"
        "rhythmCurve.suggestedHookCodes、worldview 造梦师与 coreNouns.tier 等已对齐字段。"
        "输出完整 structure-plan 对象 JSON，无 markdown。"
    ),
    "character-generator": (
        "你是短剧人物编剧（对齐 character-designer）。根据 projectBrief 与 structurePlan 生成"
        "character-bible JSON。至少 1 主角、1 反派、2 配角；每角色必填："
        "id/name/roleType/age/gender/archetypeCode、appearance≥20 字、"
        "surfacePersonality、realPersonality、background、coreMotivation、"
        "shortTermGoal、longTermGoal、secret、weakness、"
        "characterArc（startingState/keyTurningPoints≥2/finalState）、"
        "signatureLines≥3、iconicProps≥1、speechPatterns≥2、"
        "voiceProfile（label/pitch/pace/summary，summary 含 AI配音参考）、"
        "behaviorProfile（catchphrase/habit/languageStyle≥2/decisionLogic≥2/"
        "behaviorFeatures≥2/likes/dislikes）、"
        "visualAnchor（distinctiveFeatures/clothingStyle/habitGestures/consistencyRules≥1）。"
        "配角可加 contrastRelation（contrastType/contrastDescription）。"
        "顶层含 creativeDna：antiClicheElements≥1（code/label/effect）、"
        "uniqueSettings≥1（code/label/example）、aiAuthenticityNotes≥2。"
        "输出含 protagonists/antagonists/supportingRoles/relationshipMap/summary 的完整对象。只输出 JSON。"
    ),
    "relationship-weaver": (
        "你是人物关系编剧。根据既有 characterBible 补全 relationshipMap 与 relationshipSummary。"
        "至少 3 组关系；每组必填 characterAId、characterBId、characterAName、characterBName"
        "（ID 须与角色 id 一致，姓名与 name 一致）、relationType、description≥30 字、"
        "evolutionPath、perspectiveA（A 如何看待 B）、perspectiveB（B 如何看待 A）、"
        "coreConflict、hiddenTension。只输出 JSON："
        "{\"relationshipMap\": [...], \"relationshipSummary\": \"...\"}。"
    ),
    "hook-planner": (
        "你是短剧创作规划师（合并 hook/reversal/psychology/payment 规划）。"
        "根据 projectBrief、structurePlan、characterBible 与 knowledgeReferences 输出："
        "creativePlan：hookDiversity（maxSameTypeInRow/forbidAdjacentSameStrength/requiredTypes，"
        "requiredTypes 引用 hook-types-library 代码前缀如 HOOK-SLAP）、"
        "paymentCheckpoints（totalEpisodes≥30 时第 8/9/10 集各 1 条，marker 取 paywall|strong-hook|cliffhanger）、"
        "reversalSchedule（对齐 structurePlan.keyReversalPoints，每项含 episode/type/note，"
        "尽量带 reversalCode 对照 reversal-patterns-library）、"
        "psychologyStrategy（dominantArchetype、audiencePainPoint、informationGapStrategy、"
        "satisfactionRhythm、notes≥40 字）；"
        "stageIndex 恰好 6 项（与 sixStagePlan 集数范围对齐）；"
        "keyHighlights 全剧 5-8 个（含 episode/type/title/description）。只输出 JSON。"
    ),
    "framework-builder": (
        "你是短剧大纲框架编剧。frameworkOnly=true 时输出 stageBlocks 恰好 6 项（与 stageIndex 对齐）。"
        "每项 roughOutline 仅写本阶段整体方向（80-400 字）：核心任务、情绪基调、阶段收束，"
        "禁止按 Ep1/Ep2/第N集 逐集罗列，禁止写分集梗概/钩子/反转（分集内容由 episode-outline-writer 生成）。"
        "singleStageOnly=true 时只输出 targetStageKey 对应的一项 stageBlocks。"
        "可同时输出 keyHighlights。episodes=[]。只输出 JSON。"
    ),
    "episode-outline-writer": (
        "你是分集大纲编剧。只输出单集 episodes 数组（长度=1），"
        "oneLineSummary 100-200 字，hook/reversal/cliffhanger 各≥20 字，"
        "含 stageInfo、hookTypeCode（对照 hook-types-library）、"
        "reversalCode（对照 reversal-patterns-library，若本集有反转）。"
        "只输出 JSON。"
    ),
    "plan-fixer": (
        "你是大纲修复编辑。根据 sub-plan 校验 issues 修复 series-outline JSON。"
        "保留已有合理内容。输出完整 series-outline 对象。只输出 JSON。"
    ),
    "episode-script-writer": (
        "你是竖屏短剧编剧（对齐 script-creator-core）。根据 seriesOutline、characterBible"
        "与 knowledgeReferences 生成指定集数 episodes JSON。"
        "每集：scenes≤3，竖屏 90 秒三段式（hook 0-10s / 升级 10-70s / 卡点 70-90s）；"
        "sceneHeading 含景别与内外景；dialogues 单句≤40 字、口语化，角色语气贴合"
        "voiceProfile/behaviorProfile/speechPatterns，禁止 OOC；"
        "actions 简洁可拍；须引用当集大纲的 hookTypeCode（若有）并在开场体现；"
        "若大纲含 reversalCode 须在当集 reversal 段落体现；"
        "生成 scriptMarkdown（标准竖屏剧本 Markdown）。只输出 JSON。"
    ),
}


def _deep_merge(base: dict, patch: dict) -> dict:
    out = dict(base or {})
    for key, val in (patch or {}).items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


@dataclass
class TraceEntry:
    id: str
    status: str
    type: str = ""
    cli: str = ""
    script: str = ""
    message: str = ""


@dataclass
class SkillExecutionState:
    agent_id: str
    entries: List[TraceEntry] = field(default_factory=list)

    def record(
        self,
        skill_id: str,
        status: str,
        *,
        skill_type: str = "",
        cli: str = "",
        script: str = "",
        message: str = "",
    ) -> None:
        for existing in self.entries:
            if existing.id == skill_id:
                existing.status = status
                existing.message = message or existing.message
                return
        self.entries.append(
            TraceEntry(
                id=skill_id,
                status=status,
                type=skill_type,
                cli=cli,
                script=script,
                message=message,
            )
        )

    def executed_ids(self) -> List[str]:
        return [e.id for e in self.entries if e.status == "executed"]

    def to_trace_list(self, agent_id: str) -> List[Dict[str, str]]:
        from apps.agent.runtime import get_agent

        recorded = {e.id: e for e in self.entries}
        agent = get_agent(agent_id) or {}
        defined = {
            s.get("id"): s for s in (agent.get("sub_skills") or []) if isinstance(s, dict)
        }
        trace: List[Dict[str, str]] = []
        for entry in self.entries:
            trace.append(
                {
                    "id": entry.id,
                    "type": entry.type,
                    "cli": entry.cli,
                    "script": entry.script,
                    "status": entry.status,
                    "message": entry.message,
                }
            )
        for skill_id, meta in defined.items():
            if skill_id not in recorded:
                trace.append(
                    {
                        "id": skill_id,
                        "type": str(meta.get("type") or ""),
                        "cli": str(meta.get("cli") or ""),
                        "script": str(meta.get("script") or ""),
                        "status": "skipped",
                        "message": "",
                    }
                )
        return trace


class SubSkillOrchestrator:
    def __init__(self, orch: FusionOrchestrator, agent_id: str):
        self.orch = orch
        self.agent_id = agent_id
        self.project = orch.project
        self.state = SkillExecutionState(agent_id=agent_id)

    def _meta(self, skill_id: str) -> Dict[str, Any]:
        return sub_skill_meta(self.agent_id, skill_id) or {}

    def _record_from_meta(
        self,
        skill_id: str,
        status: str,
        message: str = "",
        *,
        input_summary: Optional[Dict[str, Any]] = None,
        output_summary: Optional[Dict[str, Any]] = None,
        output_payload: Any = None,
        duration_ms: Optional[int] = None,
        node_id: str = "",
        upstream: Optional[Dict[str, Any]] = None,
    ) -> None:
        meta = self._meta(skill_id)
        self.state.record(
            skill_id,
            status,
            skill_type=str(meta.get("type") or ""),
            cli=str(meta.get("cli") or ""),
            script=str(meta.get("script") or ""),
            message=message,
        )
        from ..monitoring.execution_run_service import AgentExecutionRunService

        AgentExecutionRunService.record_sub_skill(
            skill_id,
            status,
            skill_type=str(meta.get("type") or ""),
            cli=str(meta.get("cli") or ""),
            script=str(meta.get("script") or ""),
            message=message,
            input_summary=input_summary,
            output_summary=output_summary,
            output_payload=output_payload,
            duration_ms=duration_ms,
            node_id=node_id,
            upstream=upstream,
        )

    def run_reference_injector(self, upstream: Dict[str, Any]) -> Dict[str, Any]:
        skill_id = "reference-injector"
        try:
            out = inject_knowledge_upstream(self.agent_id, dict(upstream), self.project)
            self._record_from_meta(skill_id, "executed")
            return out
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] %s failed: %s", self.agent_id, skill_id, exc)
            self._record_from_meta(skill_id, "failed", str(exc)[:200])
            return dict(upstream)

    def run_llm_sub_skill(
        self,
        skill_id: str,
        node_id: str,
        upstream: Dict[str, Any],
        *,
        token_key: Optional[str] = None,
    ) -> dict:
        if not LlmService.is_enabled():
            raise LlmServiceError(
                f"{skill_id} 需要 LLM：请设置 FUSION_LLM_ENABLED=true 并配置大模型"
            )
        meta = self._meta(skill_id)
        system, user = self.orch.prompts.build_sub_skill(
            node_id,
            skill_id,
            meta,
            upstream,
            system_hint=_SUB_SKILL_SYSTEM_HINTS.get(skill_id, ""),
        )
        from apps.workflow.step_admin import PipelineStepAdminService

        from apps.skill.llm.usage_log import llm_usage_scope
        from apps.skill.models import LlmUsageLog

        provider_id = PipelineStepAdminService.resolve_provider_id(node_id)
        max_tokens = resolve_agent_max_tokens(token_key or self.agent_id)
        if skill_id == "character-generator":
            max_tokens = max(max_tokens, 16384)
        from ..monitoring.execution_run_service import get_active_run_id

        started = time.monotonic()
        try:
            with llm_usage_scope(
                source_type=LlmUsageLog.SOURCE_NODE,
                source_key=f"{node_id}:{skill_id}"[:64],
                project_id=self.orch.project.id,
                user_id=self.orch.project.user_id,
                execution_run_id=get_active_run_id(),
                sub_skill_id=skill_id,
            ):
                payload = LlmService.generate_json(
                    system_prompt=system,
                    user_prompt=user,
                    provider_id=provider_id,
                    max_tokens=max_tokens,
                )
            duration_ms = int((time.monotonic() - started) * 1000)
            raw = payload if isinstance(payload, dict) else {}
            result = unwrap_llm_payload(skill_id, raw)
            self._record_from_meta(
                skill_id,
                "executed",
                duration_ms=duration_ms,
                node_id=node_id,
                upstream=upstream,
                output_payload=result,
            )
            return result
        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.monotonic() - started) * 1000)
            logger.exception("[%s] LLM sub-skill %s failed", self.agent_id, skill_id)
            self._record_from_meta(
                skill_id,
                "failed",
                str(exc)[:200],
                duration_ms=duration_ms,
                node_id=node_id,
                upstream=upstream,
            )
            raise

    def run_dream_indicators_normalize(self, payload: dict) -> dict:
        skill_id = "dream-indicators"
        try:
            out = normalize_structure_payload(dict(payload), self.project)
            self._record_from_meta(skill_id, "executed")
            return out
        except Exception as exc:  # noqa: BLE001
            self._record_from_meta(skill_id, "failed", str(exc)[:200])
            raise

    def run_rhythm_calibrator(self, payload: dict) -> dict:
        skill_id = "rhythm-calibrator"
        try:
            out = enrich_structure_payload(
                dict(payload),
                theme=getattr(self.project, "theme", "") or "",
                episode_count=getattr(self.project, "episode_count", None),
            )
            self._record_from_meta(skill_id, "executed")
            return out
        except Exception as exc:  # noqa: BLE001
            self._record_from_meta(skill_id, "failed", str(exc)[:200])
            raise

    def run_world_validate(self, input_path: Path, *, strict: bool = True) -> tuple[bool, List[str]]:
        skill_id = "world-validator"
        try:
            result = unwrap_fusion_cli_result(
                cli_world_validate(self.orch.runner, input_path, strict=strict)
            )
            passed = bool(result.get("passed", result.get("ok", True)))
            issues = list(result.get("issues") or result.get("errors") or [])
            if not passed and not issues:
                issues = [str(result.get("message") or "sub-world 校验未通过")]
            if passed:
                self._record_from_meta(skill_id, "executed")
            else:
                self._record_from_meta(skill_id, "failed", "; ".join(str(i) for i in issues[:3])[:200])
            return passed, issues
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)[:200]
            self._record_from_meta(skill_id, "failed", msg)
            return False, [msg]

    def run_brief_theme_matcher(self, brief: dict) -> dict:
        skill_id = "brief-theme-matcher"
        try:
            from ..trend_formula import build_trend_formula, normalize_trend_formula
            from .knowledge import retrieve_references

            theme = (brief.get("theme") or getattr(self.project, "theme", "") or "").strip()
            display = (brief.get("themeDisplayName") or "").strip()
            out = dict(brief)
            refs = retrieve_references(
                theme=theme,
                tags=["theme-templates.json", "douyin-formula-library.json"],
                limit=3,
            )
            if refs.get("blocks"):
                out["themeReferenceHints"] = refs

            existing = out.get("trendFormula")
            if not existing:
                out["trendFormula"] = build_trend_formula(theme, theme_display_name=display)
            else:
                out["trendFormula"] = normalize_trend_formula(existing, theme=theme, theme_display_name=display)

            if not out.get("writingBrief"):
                tf = out.get("trendFormula") or {}
                tone_parts = [
                    (tf.get("coreConflictFormula") or "").strip(),
                    (tf.get("audienceFit") or "").strip(),
                ]
                tone = " · ".join(p for p in tone_parts if p)
                if tone:
                    out["writingBrief"] = {"tone": tone[:500]}
            self._record_from_meta(skill_id, "executed", message=f"{len(refs.get('blocks') or [])} 参考块")
            return out
        except Exception as exc:  # noqa: BLE001
            self._record_from_meta(skill_id, "failed", str(exc)[:200])
            return brief

    def run_brief_enrich_cli(self, brief: dict, *, in_path: Path, out_path: Path) -> dict:
        skill_id = "brief-enricher"
        in_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            cli = unwrap_fusion_cli_result(
                cli_brief_enrich(self.orch.runner, in_path, output_path=out_path, strict=False)
            )
            if out_path.is_file():
                enriched = json.loads(out_path.read_text(encoding="utf-8"))
            elif isinstance(cli.get("projectBrief"), dict):
                enriched = cli["projectBrief"]
            elif isinstance(cli.get("brief"), dict):
                enriched = cli["brief"]
            elif cli.get("coreHook") or cli.get("theme"):
                enriched = cli
            else:
                enriched = brief
            self._record_from_meta(skill_id, "executed")
            return enriched
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] %s failed: %s", self.agent_id, skill_id, exc)
            self._record_from_meta(skill_id, "failed", str(exc)[:200])
            return brief

    def run_plan_validate(
        self,
        input_path: Path,
        *,
        episodes: Optional[int] = None,
        strict: bool = True,
    ) -> tuple[bool, List[str]]:
        skill_id = "plan-validator"
        try:
            result = unwrap_fusion_cli_result(
                cli_plan_validate(
                    self.orch.runner,
                    input_path,
                    episodes=episodes,
                    strict=strict,
                )
            )
            passed = bool(result.get("passed", result.get("ok", True)))
            issues = list(result.get("issues") or result.get("errors") or [])
            if not passed and not issues:
                issues = [str(result.get("message") or "sub-plan 校验未通过")]
            if passed:
                self._record_from_meta(skill_id, "executed")
            else:
                self._record_from_meta(skill_id, "failed", "; ".join(str(i) for i in issues[:3])[:200])
            return passed, issues
        except Exception as exc:  # noqa: BLE001
            self._record_from_meta(skill_id, "failed", str(exc)[:200])
            return False, [str(exc)]

    def run_plan_fixer(self, payload: dict, issues: List[str], node_id: str) -> dict:
        skill_id = "plan-fixer"
        upstream = {"validationIssues": issues[:20], "seriesOutline": payload}
        try:
            patch = self.run_llm_sub_skill(skill_id, node_id, upstream, token_key="outline_framework")
            patch = extract_fixer_patch(skill_id, patch)
            if not fixer_patch_meaningful(patch):
                self._record_from_meta(skill_id, "failed", "fixer 未返回有效补丁")
                return payload
            return _deep_merge(payload, patch)
        except Exception as exc:  # noqa: BLE001
            self._record_from_meta(skill_id, "failed", str(exc)[:200])
            return payload

    def run_world_fixer(self, payload: dict, issues: List[str], node_id: str) -> dict:
        skill_id = "world-fixer"
        upstream = {
            "validationIssues": issues[:20],
            "structurePlan": payload,
            "projectBrief": payload.get("projectBrief"),
        }
        try:
            patch = self.run_llm_sub_skill(skill_id, node_id, upstream, token_key="world")
            patch = extract_fixer_patch(skill_id, patch)
            if not fixer_patch_meaningful(patch):
                self._record_from_meta(skill_id, "failed", "fixer 未返回有效补丁")
                return payload
            merged = _deep_merge(payload, patch)
            schema_file = "structure-plan.schema.json"
            ok, msgs = validate_against_schema(
                merged, f"schemas/{schema_file}", config=self.orch.config
            )
            if not ok:
                logger.warning("[WorldAgent] fixer schema warnings: %s", msgs[:3])
            return merged
        except Exception as exc:  # noqa: BLE001
            self._record_from_meta(skill_id, "failed", str(exc)[:200])
            return payload
