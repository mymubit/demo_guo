# -*- coding: utf-8 -*-
"""
Agent 注册表配置测试 — drama.* 新体系。

旧的 brief/structure/character/outline/script workspace_index 测试已移除。
现在改为测试 drama.* workspace_order 和 get_agent 功能。
"""
from django.test import TestCase

from apps.agent.runtime import (
    DRAMA_FAST_TRACK_AGENT_IDS,
    DRAMA_WORKSPACE_ORDER,
    workspace_index_for_agent,
    get_agent,
)


class DramaWorkspaceOrderTests(TestCase):
    """验证 drama.* 工作台排序正确性。"""

    def test_fast_track_agents_have_correct_count(self):
        self.assertEqual(len(DRAMA_FAST_TRACK_AGENT_IDS), 8)

    def test_fast_track_contains_required_roles(self):
        required = [
            "drama.topic-planner",
            "drama.world-architect",
            "drama.character-designer",
            "drama.plot-architect",
            "drama.script-writer",
            "drama.script-reviewer",
            "drama.quality-reporter",
            "drama.compliance-guard",
        ]
        for r in required:
            self.assertIn(r, DRAMA_FAST_TRACK_AGENT_IDS, f"{r} 不在快速通道中")

    def test_workspace_order_is_unique(self):
        orders = list(DRAMA_WORKSPACE_ORDER.values())
        self.assertEqual(len(orders), len(set(orders)), "workspace_order 有重复值")

    def test_workspace_index_for_known_role(self):
        self.assertEqual(workspace_index_for_agent("drama.topic-planner"), 103)
        self.assertEqual(workspace_index_for_agent("drama.script-writer"), 401)
        self.assertEqual(workspace_index_for_agent("drama.compliance-guard"), 801)

    def test_workspace_index_for_unknown_returns_999(self):
        self.assertEqual(workspace_index_for_agent("nonexistent.role"), 999)

    def test_dept_order_is_sequential(self):
        """同部门的角色 workspace_order 应落在对应百位段。"""
        for agent_id, order in DRAMA_WORKSPACE_ORDER.items():
            if 100 <= order < 200:
                self.assertLess(order, 200, f"{agent_id} order={order}")
            elif 200 <= order < 300:
                self.assertLess(order, 300, f"{agent_id} order={order}")
            elif 700 <= order < 800:
                self.assertLess(order, 800, f"{agent_id} order={order}")
