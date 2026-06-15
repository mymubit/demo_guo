# -*- coding: utf-8 -*-
"""WorldAgent：六阶段结构 + 世界观 + sub-world 校验（SubSkillOrchestrator 编排）。"""
from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from apps.workflow.fusion.schema_validator import validate_against_schema

from ..pipeline_debug_log import log_fusion_node_begin, summarize_artifact
from ..display.structure_display import validate_worldview_issues
from .sub_skill_orchestrator import FIXER_MAX_ROUNDS, SubSkillOrchestrator, _deep_merge
from .verify_creation_support import run_reference_verify_if_needed

if TYPE_CHECKING:
    from ..fusion.fusion_orchestrator import FusionOrchestrator

logger = logging.getLogger(__name__)

NODE_ID = "node-2-structure"
AGENT_ID = "world"
SCHEMA_FILE = "structure-plan.schema.json"

# P1 设定级合规扫描规则（总典第四层，世界观层检测）
# 格式：(regex, label, required_constraint)
_WORLD_P1_RULES: Tuple[Tuple[str, str, str], ...] = (
    (
        r"灵异|鬼怪|鬼魂|亡灵|阴间|地府|降头|巫术|通灵|附身",
        "灵异/超自然设定",
        "须有科学/现实解释或正义收束；禁止宣扬封建迷信为客观事实",
    ),
    (
        r"真实历史人物|历史名人|[皇帝|太后|慈禧|秦始皇|武则天|雍正|乾隆]",
        "真实历史人物",
        "须架空处理，禁止直接使用真实历史人物姓名及事件",
    ),
    (
        r"黑社会|黑帮|地下势力|犯罪组织|毒枭|洗钱",
        "涉黑/犯罪组织设定",
        "犯罪组织必须在结局受到法律制裁；禁止美化黑帮文化",
    ),
    (
        r"赌博|赌场|地下钱庄|高利贷",
        "赌博/高利贷设定",
        "须有明确负面后果；禁止展示赌博赢钱的正面结果",
    ),
    (
        r"自杀|轻生|割腕|跳楼.*(?:死|亡)|结束.*生命",
        "自杀/自伤设定",
        "须有危机干预/求生意志转变；禁止美化或示范自杀行为",
    ),
    (
        r"邪教|传销|洗脑组织|末日邪教",
        "邪教/传销设定",
        "须明确定性为违法组织；结局必须被依法取缔",
    ),
)


def _scan_world_compliance(payload: dict) -> List[Dict[str, Any]]:
    """
    扫描生成的世界观文本，返回 P1 合规警告列表。
    不阻断生成，但结果写入 worldValidationLog 供人工审查和进化审计使用。
    """
    worldview = payload.get("worldview") or {}
    scan_text = " ".join(filter(None, [
        worldview.get("settingSummary") or "",
        " ".join(worldview.get("rootRules") or []),
        payload.get("workingTitle") or "",
        payload.get("coreStoryArc", {}).get("openingSetup") if isinstance(payload.get("coreStoryArc"), dict) else "",
    ]))

    warnings = []
    for pattern, label, constraint in _WORLD_P1_RULES:
        if re.search(pattern, scan_text, flags=re.IGNORECASE):
            warnings.append({
                "level": "P1",
                "category": label,
                "constraint": constraint,
                "source": "world-compliance-scan",
            })
    return warnings


class WorldAgentEngine:
    def __init__(self, orch: FusionOrchestrator):
        self.orch = orch
        self.project = orch.project
        self.orchestrator = SubSkillOrchestrator(orch, AGENT_ID)
        self.executed_skills: List[str] = []

    def _sync_executed(self) -> None:
        self.executed_skills = self.orchestrator.state.executed_ids()

    def _write_structure_file(self, payload: dict):
        path = self.orch.work_dir / f"{self.project.id.hex}_structure.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _validate_schema(self, payload: dict) -> None:
        ok, msgs = validate_against_schema(
            payload, f"schemas/{SCHEMA_FILE}", config=self.orch.config
        )
        if not ok:
            logger.warning(
                "[WorldAgent] schema 警告: %s output=%s",
                msgs[:5],
                summarize_artifact("structure_plan", payload),
            )
            if self.orch.strict_schema:
                raise ValueError(f"{NODE_ID} schema 校验失败: {'; '.join(msgs[:5])}")

    def generate(self, artifacts: Dict[str, Any]) -> dict:
        self.orch._mark_node_running(NODE_ID)
        self.orch._flush_progress(
            node_id=NODE_ID,
            summary="WorldAgent · 六阶段结构与世界观",
            sub_pct=10,
        )

        orch = self.orchestrator
        upstream = {"projectBrief": artifacts["project_brief"]}
        upstream = orch.run_reference_injector(upstream)

        log_fusion_node_begin(
            project_id=self.project.id,
            node_id=NODE_ID,
            node_index=self.orch._node_index(NODE_ID),
            upstream={"agentId": AGENT_ID, **upstream},
            prompt_stats={"mode": "sub-skill-orchestrator", "step": "structure-generator"},
        )

        structure_part = orch.run_llm_sub_skill(
            "structure-generator",
            NODE_ID,
            upstream,
            token_key=AGENT_ID,
        )

        builder_upstream = {
            **upstream,
            "structurePlan": structure_part,
        }
        world_part = orch.run_llm_sub_skill(
            "world-builder",
            NODE_ID,
            builder_upstream,
            token_key=AGENT_ID,
        )

        payload = _deep_merge(structure_part, world_part)
        payload = orch.run_dream_indicators_normalize(payload)
        payload = orch.run_rhythm_calibrator(payload)
        self._validate_schema(payload)

        path = self._write_structure_file(payload)
        passed, issues = orch.run_world_validate(path, strict=True)

        for _ in range(FIXER_MAX_ROUNDS):
            if passed:
                break
            payload = orch.run_world_fixer(payload, issues, NODE_ID)
            payload = orch.run_dream_indicators_normalize(payload)
            payload = orch.run_rhythm_calibrator(payload)
            path = self._write_structure_file(payload)
            passed, issues = orch.run_world_validate(path, strict=True)

        if not passed:
            logger.warning(
                "[WorldAgent] sub-world 校验未完全通过，保留最佳努力产物: %s",
                issues[:5],
            )

        payload = self.orchestrator.run_dream_indicators_normalize(payload)
        post_issues = validate_worldview_issues(payload)
        cli_issues = list(issues) if not passed else []
        merged_issues = list(dict.fromkeys(cli_issues + post_issues))

        # P1 设定合规扫描（总典第四层·世界观层）
        compliance_warnings = _scan_world_compliance(payload)
        if compliance_warnings:
            logger.warning(
                "[WorldAgent] P1合规警告 project=%s count=%d categories=%s",
                self.project.id,
                len(compliance_warnings),
                [w["category"] for w in compliance_warnings],
            )

        payload["worldValidationLog"] = {
            "passed": passed and len(post_issues) == 0,
            "issues": merged_issues,
            "checker": "sub-world",
            "complianceWarnings": compliance_warnings,
            "complianceLevel": "P1" if compliance_warnings else "clear",
        }
        if not passed and not post_issues:
            logger.info("[WorldAgent] sub-world CLI 未通过，归一化后 Python 校验已通过")
        run_reference_verify_if_needed(self.orch, artifact="world", payload=payload)
        self._sync_executed()
        return payload
