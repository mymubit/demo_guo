# -*- coding: utf-8 -*-
"""
Tier1 区块配置测试 — drama.* 新体系。

旧的 agent_id_for_fusion_node、node_structure/node_script 等测试已移除。
"""
from django.test import SimpleTestCase

from apps.agent.bootstrap.tier1_sections import (
    AGENT_TIER1_SEED,
    resolve_tier1_sections,
)


class DramaTier1SectionsTest(SimpleTestCase):
    """验证 drama.* 角色的 Tier1 区块映射正确性。"""

    def test_script_writer_has_required_sections(self):
        sections = resolve_tier1_sections("drama.script-writer")
        self.assertIn("format_standard", sections)
        self.assertIn("writing_prohibitions", sections)
        self.assertIn("hook_effectiveness", sections)

    def test_plot_architect_has_structure_sections(self):
        sections = resolve_tier1_sections("drama.plot-architect")
        self.assertIn("episode_structure", sections)
        self.assertIn("rhythm_rules", sections)
        self.assertIn("qdn_emotion_model", sections)

    def test_quality_reporter_has_scoring(self):
        sections = resolve_tier1_sections("drama.quality-reporter")
        self.assertIn("scoring", sections)

    def test_compliance_guard_has_scoring(self):
        sections = resolve_tier1_sections("drama.compliance-guard")
        self.assertIn("scoring", sections)

    def test_emotion_architect_has_emotion_sections(self):
        sections = resolve_tier1_sections("drama.emotion-architect")
        self.assertIn("episode_emotion_8nodes", sections)
        self.assertIn("qdn_emotion_model", sections)
        self.assertIn("emotion_externalization_dict", sections)

    def test_unknown_agent_returns_empty(self):
        sections = resolve_tier1_sections("drama.nonexistent-role")
        self.assertEqual(sections, [])

    def test_all_drama_roles_are_mapped(self):
        """所有 drama.* 角色都应有 Tier1 映射。"""
        from apps.drama.defaults import DRAMA_ROLE_DEFAULTS
        for role in DRAMA_ROLE_DEFAULTS:
            agent_id = role["agent_id"]
            # 可以为空列表，但 key 必须存在
            self.assertIn(
                agent_id, AGENT_TIER1_SEED,
                f"drama role {agent_id} 缺少 Tier1 区块映射",
            )
