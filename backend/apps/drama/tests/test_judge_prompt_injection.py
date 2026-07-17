# -*- coding: utf-8 -*-
"""裁判角色（评分官/合规官）规则注入与评分细则内联。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.prompt_builder import PromptBuilder
from apps.drama.services.skills_loader import SkillsBundleLoader
from apps.drama.tests.helpers import SKILLS_ROOT

_SETTINGS = {
    "title": "测试剧",
    "target_platform": "douyin",
    "entry_type": "original",
    "creation_preferences": {"scoring_preset": "standard"},
    "genre_matrix": {
        "emotion": "revenge",
        "identity": "underdog",
        "conflict": "power",
        "world": "modern",
        "audience_channel": "female",
    },
}


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class JudgeRuleInjectionTests(SimpleTestCase):
    def setUp(self) -> None:
        self.loader = SkillsBundleLoader(root=SKILLS_ROOT)

    def test_script_scorer_keeps_scoring_rules_drops_writing_noise(self) -> None:
        text = self.loader.collect_rules(
            "drama.script-scorer",
            _SETTINGS,
            max_chars=3600,
        )
        self.assertIn("十维权重摘要", text)
        self.assertIn("S级一票否决", text)
        self.assertIn("G-Eval", text)
        self.assertNotIn("AI 腔禁用词", text)
        self.assertNotIn("台词行动意图", text)

    def test_compliance_guard_keeps_compliance_core_drops_writing_noise(self) -> None:
        text = self.loader.collect_rules(
            "drama.compliance-guard",
            _SETTINGS,
            max_chars=3200,
        )
        self.assertIn("九维风险评估", text)
        self.assertIn("P2 建议优化", text)
        self.assertIn("三阶段合规检查", text)
        self.assertIn("平台专项检查", text)
        self.assertNotIn("AI 腔禁用词", text)
        self.assertNotIn("LR-001", text)

    def test_script_scorer_prompt_inlines_quality_scoring_dimensions(self) -> None:
        builder = PromptBuilder(loader=self.loader)
        system, _user = builder.build(
            "drama.script-scorer",
            settings=_SETTINGS,
            workflow_state={},
            artifacts={},
            latest_script={
                "resolved_script_key": "external_script",
                "value": {"episodes": [{"script": "第一集"}]},
            },
            scoring_mode="external",
        )
        self.assertIn("## 评分细则（内联）", system)
        self.assertIn("叙事效率", system)
        self.assertIn("付费点优化", system)
        self.assertIn("0.15", system)
        self.assertIn("scoring_preset=standard", system)
        self.assertIn("evidence", system)
        self.assertIn("deductions", system)

    def test_scorer_prompt_includes_quality_report_skeleton_keys(self) -> None:
        builder = PromptBuilder(loader=self.loader)
        system, _ = builder.build(
            "drama.script-scorer",
            settings=_SETTINGS,
            workflow_state={},
            artifacts={},
            latest_script={
                "resolved_script_key": "external_script",
                "value": {"episodes": [{"script": "x"}]},
            },
            scoring_mode="external",
        )
        self.assertIn("evidence", system)
        self.assertIn("deductions", system)
        self.assertIn("dimensions", system)
        self.assertRegex(system, r"format|hooks|genre_fit")

        # render_contract_block 专有标记；_output_schema_hints 无法单独满足
        self.assertIn("最小合法示例", system)
        self.assertIn("  - dimensions.format", system)
        self.assertIn("  - dimensions.hooks", system)

        contract_anchor = system.index("最小合法示例")
        json_fence = system.index("```json", contract_anchor)
        json_end = system.index("```", json_fence + len("```json"))
        json_example = system[json_fence:json_end]
        self.assertIn('"format"', json_example)
        self.assertIn('"evidence"', json_example)
        self.assertIn('"dimensions"', json_example)

    def test_scorer_rules_fit_budget_without_truncating_core(self) -> None:
        text = self.loader.collect_rules(
            "drama.script-scorer", _SETTINGS, max_chars=3600
        )
        self.assertNotIn("...", text[-5:])  # 核心规则应完整装入；若仍截断需先提 max_chars 再测
        self.assertIn("十维权重摘要", text)
        self.assertIn("S级一票否决", text)

    def test_compliance_prompt_keeps_nine_dimension_and_phases(self) -> None:
        text = self.loader.collect_rules(
            "drama.compliance-guard", _SETTINGS, max_chars=3200
        )
        self.assertIn("九维风险评估", text)
        self.assertIn("三阶段合规检查", text)
        self.assertIn("P2 建议优化", text)
