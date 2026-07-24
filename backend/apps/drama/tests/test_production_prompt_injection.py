# -*- coding: utf-8 -*-
"""生产角色规则注入收窄：sections 落地后不得再灌写作/评分噪声。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.skills_loader import SkillsBundleLoader
from apps.drama.tests.helpers import SKILLS_ROOT

_SETTINGS = {
    "title": "测试剧",
    "target_platform": "generic",
    "entry_type": "original_track",
    "creation_preferences": {"scoring_preset": "standard"},
    "genre_matrix": {
        "emotion": "warmth",
        "identity": "urban",
        "conflict": "family",
        "world": "realistic",
    },
}


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class ProductionRuleInjectionTests(SimpleTestCase):
    def setUp(self) -> None:
        self.loader = SkillsBundleLoader(root=SKILLS_ROOT)

    def test_topic_director_keeps_playbook_drops_writing_scoring_noise(self) -> None:
        text = self.loader.collect_rules(
            "drama.topic-director",
            _SETTINGS,
        )
        self.assertIn("选题定调必须吸收市场判断", text)
        self.assertIn("五类创意入口", text)
        self.assertNotIn("AI 腔禁用词", text)
        self.assertNotIn("台词行动意图", text)
        self.assertNotIn("G-Eval", text)

    def test_story_bible_keeps_structure_drops_ai_tone(self) -> None:
        text = self.loader.collect_rules(
            "drama.story-bible",
            _SETTINGS,
        )
        self.assertTrue(
            "六阶段" in text
            or "角色密度" in text
            or "年龄段" in text
            or "伏笔" in text
            or "冲突" in text,
            msg=f"expected structure/character rules, got snippet: {text[:400]}",
        )
        self.assertNotIn("AI 腔禁用词", text)

    def test_script_writer_keeps_dialogue_drops_compliance_core(self) -> None:
        text = self.loader.collect_rules(
            "drama.script-writer",
            _SETTINGS,
        )
        self.assertTrue(
            "AI 腔" in text or "台词" in text or "格式禁止" in text,
            msg=f"expected writing rules, got snippet: {text[:400]}",
        )
        self.assertNotIn("九维风险评估", text)

    def test_production_roles_declare_sections(self) -> None:
        for agent_id in (
            "drama.topic-director",
            "drama.story-bible",
            "drama.episode-designer",
            "drama.script-writer",
            "drama.revision-master",
            "drama.delivery-tool",
        ):
            contract = self.loader.get_role_contract(agent_id)
            sections = (contract.get("rule_policy") or {}).get("sections") or []
            self.assertTrue(
                sections,
                msg=f"{agent_id} missing rule_policy.sections",
            )

    def test_tear_down_skipped_without_reference_dramas(self) -> None:
        assembled = self.loader.assemble_modules_for_role(
            "drama.topic-director", _SETTINGS
        )
        included = {m["id"] for m in assembled["included"]}
        skipped = {m["id"]: m for m in assembled["skipped"]}
        self.assertNotIn("tear-down-6d", included)
        self.assertEqual(skipped.get("tear-down-6d", {}).get("reason"), "enable_when")

    def test_tear_down_enable_when_passes_with_reference_dramas(self) -> None:
        """有 reference_dramas 时不得因 enable_when 跳过；预算裁切可接受。"""
        settings = {**_SETTINGS, "reference_dramas": ["某热播剧"]}
        assembled = self.loader.assemble_modules_for_role(
            "drama.topic-director", settings
        )
        included = {m["id"] for m in assembled["included"]}
        skipped = {m["id"]: m for m in assembled["skipped"]}
        if "tear-down-6d" in included:
            return
        self.assertIn("tear-down-6d", skipped)
        self.assertEqual(skipped["tear-down-6d"]["reason"], "budget")
