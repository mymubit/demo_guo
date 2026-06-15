# -*- coding: utf-8 -*-
"""BriefAgent 执行引擎：立项字段 + sub-brief CLI 补全（SubSkillOrchestrator）。"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Dict, List

from apps.workflow.fusion.schema_registry import FusionSchemaRegistry
from apps.workflow.fusion.schema_validator import validate_against_schema

from ..compliance_fuse import run_compliance_fuse_scan
from ..schema_mappers import build_project_brief, enrich_brief_from_form_seed
from .sub_skill_orchestrator import SubSkillOrchestrator

if TYPE_CHECKING:
    from ..fusion.fusion_orchestrator import FusionOrchestrator

logger = logging.getLogger(__name__)

NODE_ID = "node-1-input"
AGENT_ID = "brief"

# P0 题材级关键词——出现即熔断，不进行任何生成
_BRIEF_P0_PATTERNS = (
    (r"台独|港独|藏独|疆独|法轮功|六四|天安门事件|颠覆政权|分裂国家|历史虚无主义", "政治敏感题材"),
    (r"儿童(?:色情|性|性爱)|未成年.*性爱|恋童", "未成年人危害"),
    (r"邪教|法轮|召唤恶魔|撒旦崇拜", "邪教/极端内容"),
    (r"制(?:毒|炸弹|枪).*(?:教程|方法|步骤)|杀人.*(?:教程|方法|步骤)", "犯罪教唆"),
    (r"拐卖(?:妇女|儿童|人口)|人口贩卖|买卖人口|地下器官", "人口买卖/器官黑市"),
    (r"恐怖(?:袭击|主义|组织)|极端主义.*(?:宣扬|招募)|煽动种族(?:灭绝|屠杀)", "恐怖主义/极端主义"),
)

# P1 题材级警告——不熔断，但在 brief 中注入合规提示
_BRIEF_P1_WARNINGS = (
    (r"灵异|鬼怪|鬼魂|附身|降头|阴阳|通灵", "灵异题材（须正义收束，禁止宣扬封建迷信）"),
    (r"赌博|赌场|地下赌", "赌博题材（须有明确负面后果，禁止美化）"),
    (r"黑社会|黑帮|地下势力", "涉黑题材（须有正义结局，犯罪须受到法律制裁）"),
    (r"自杀|轻生|结束生命", "自杀相关（须有危机干预/求生意志，禁止美化）"),
)


def _check_brief_compliance(project: Any) -> Dict[str, Any]:
    """
    题材级 P0 合规预检。
    返回 {"passed": True} 或 {"passed": False, "level": "P0", "reason": str}。
    """
    topic_text = " ".join(filter(None, [
        getattr(project, "theme", "") or "",
        getattr(project, "core_idea", "") or "",
        getattr(project, "title", "") or "",
    ]))

    # P0：触发即熔断
    for pattern, label in _BRIEF_P0_PATTERNS:
        if re.search(pattern, topic_text, flags=re.IGNORECASE):
            return {
                "passed": False,
                "level": "P0",
                "category": label,
                "reason": f"题材触碰P0红线（{label}），无法创作。请调整创意方向。",
            }

    # 补充：运行 compliance_fuse 文本扫描（覆盖更多模式）
    fuse_result = run_compliance_fuse_scan(topic_text)
    if fuse_result.get("fuseTriggered"):
        issues = "；".join(fuse_result.get("issues") or ["未知违规"])
        return {
            "passed": False,
            "level": "P0",
            "category": "compliance-fuse",
            "reason": f"题材描述触碰违禁内容：{issues}。请修改创意描述后重新创作。",
        }

    # P1：收集警告，不熔断
    warnings = []
    for pattern, note in _BRIEF_P1_WARNINGS:
        if re.search(pattern, topic_text, flags=re.IGNORECASE):
            warnings.append(note)

    return {"passed": True, "warnings": warnings}


class BriefAgentEngine:
    def __init__(self, orch: FusionOrchestrator):
        self.orch = orch
        self.project = orch.project
        self.orchestrator = SubSkillOrchestrator(orch, AGENT_ID)
        self.executed_skills: List[str] = []

    def _sync_executed(self) -> None:
        self.executed_skills = self.orchestrator.state.executed_ids()

    def _needs_enrich(self, brief: dict) -> bool:
        if not brief.get("trendFormula"):
            return True
        wb = brief.get("writingBrief")
        if not isinstance(wb, dict) or not (wb.get("tone") or "").strip():
            return True
        hook = (brief.get("coreHook") or self.project.core_idea or "").strip()
        return len(hook) < 5

    def generate(self, artifacts: Dict[str, Any]) -> dict:
        self.orch._mark_node_running(NODE_ID)
        orch = self.orchestrator

        # ── P0 合规预检（题材级，前置熔断，不消耗任何 LLM token）──
        compliance = _check_brief_compliance(self.project)
        orch.state.record("brief-compliance-precheck", "executed", skill_type="rule")
        if not compliance["passed"]:
            raise ValueError(compliance["reason"])
        if compliance.get("warnings"):
            logger.warning(
                "[BriefAgent] P1合规警告 project=%s warnings=%s",
                self.project.id,
                compliance["warnings"],
            )
        orch.state.record("brief-form-collector", "executed", skill_type="rule")

        existing = None if self.orch.dry_run else artifacts.get("project_brief")
        brief = existing or build_project_brief(
            self.project,
            submit_data={
                "target_platform": self.orch.catalog.normalize_platform(self.project.target_platform),
                "budget_level": self.project.budget_level,
                "creation_entry": self.project.creation_entry,
            },
            status="confirmed",
        )
        brief["targetPlatform"] = self.orch.catalog.normalize_platform(
            brief.get("targetPlatform") or self.project.target_platform
        )
        brief["formatVariant"] = self.orch.catalog.format_variant_schema_key(
            self.project.format_variant
        )
        brief["themeDisplayName"] = self.orch.catalog.theme_display_name(brief.get("theme", ""))

        brief = orch.run_brief_theme_matcher(brief)
        from ..theme_recommender import merge_theme_recommendations

        brief = merge_theme_recommendations(brief)
        orch.state.record("theme-recommender", "executed", skill_type="rule", message="题材推荐")

        if self._needs_enrich(brief):
            in_path = self.orch.work_dir / f"{self.project.id.hex}_brief_in.json"
            out_path = self.orch.work_dir / f"{self.project.id.hex}_brief_out.json"
            self.orch._flush_progress(
                node_id=NODE_ID,
                summary="BriefAgent · sub-brief 补全中…",
                sub_pct=40,
            )
            brief = orch.run_brief_enrich_cli(brief, in_path=in_path, out_path=out_path)
            brief = enrich_brief_from_form_seed(brief, self.project, submit_data={})
            brief = orch.run_brief_theme_matcher(brief)
        else:
            orch.state.record("brief-enricher", "skipped", skill_type="cli", message="字段已齐全")

        schema_reg = FusionSchemaRegistry(self.orch.config)
        schema_file = schema_reg.schema_file_for_artifact("project_brief") or "project-brief.schema.json"
        ok, msgs = validate_against_schema(brief, schema_file, config=self.orch.config)
        if not ok and self.orch.strict_schema:
            raise ValueError(f"project_brief schema 校验失败: {'; '.join(msgs)}")

        self.orch._flush_progress(
            node_id=NODE_ID,
            summary="BriefAgent · 已整理项目简报",
            sub_pct=95,
        )
        brief = enrich_brief_from_form_seed(brief, self.project, submit_data={})
        brief["agentEnriched"] = True
        self._sync_executed()
        return brief