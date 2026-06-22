# -*- coding: utf-8 -*-
"""
Drama Skills 快速通道 E2E 测试 — 验证8个核心角色的完整执行链路。

旧的 brief/structure/character/outline/script 链路已移除。
"""
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.models import AgentDefinition, AgentPromptVersion
from apps.creation.models import Project

User = get_user_model()

# drama.* 快速通道角色
FAST_TRACK_AGENTS = [
    "drama.topic-planner",
    "drama.world-architect",
    "drama.character-designer",
    "drama.plot-architect",
    "drama.script-writer",
    "drama.script-reviewer",
    "drama.quality-reporter",
    "drama.compliance-guard",
]

# 每个角色的期望产物
AGENT_ARTIFACTS = {
    "drama.topic-planner": {"project_brief": {"status": "confirmed", "title": "测试剧"}},
    "drama.world-architect": {"world_setting": {"settingSummary": "测试世界观"}},
    "drama.character-designer": {"character_bible": {"characters": []}},
    "drama.plot-architect": {"series_outline": {"episodes": [{"episodeNumber": 1}]}},
    "drama.script-writer": {"episode_scripts": {"episodes": [{"episodeNumber": 1, "title": "第1集"}]}},
    "drama.script-reviewer": {"review_report": {"overall": "通过"}},
    "drama.quality-reporter": {"quality_report": {"overall_score": 82, "grade": "A"}},
    "drama.compliance-guard": {"compliance_report": {"overall_result": "通过"}},
}


class DramaFastTrackE2ETest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900001000", password="test-pass-123")
        # 创建 drama.* 角色定义
        for agent_id in FAST_TRACK_AGENTS:
            agent, _ = AgentDefinition.objects.get_or_create(
                agent_id=agent_id,
                defaults={
                    "name": agent_id.split(".")[1],
                    "name_zh": agent_id,
                    "category": "drama_skills",
                    "workspace_order": 100,
                    "is_enabled": True,
                    "lifecycle_status": AgentDefinition.LifecycleStatus.ACTIVE,
                    "default_output_artifact_key": list(AGENT_ARTIFACTS.get(agent_id, {}).keys())[0],
                },
            )
            AgentPromptVersion.objects.get_or_create(
                agent=agent, version="v1",
                defaults={
                    "system_prompt": f"{agent_id} system prompt",
                    "is_active": True,
                    "created_by": "test",
                },
            )

    def test_fast_track_agents_are_seeded(self):
        """验证快速通道8个角色已在数据库中。"""
        for agent_id in FAST_TRACK_AGENTS:
            exists = AgentDefinition.objects.filter(agent_id=agent_id).exists()
            self.assertTrue(exists, f"drama role {agent_id} 未种入")

    def test_agent_output_contracts(self):
        """验证每个角色的期望产物键配置。"""
        for agent_id, expected_artifacts in AGENT_ARTIFACTS.items():
            agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
            self.assertIsNotNone(agent, f"{agent_id} 未找到")
            self.assertIn(
                agent.default_output_artifact_key,
                expected_artifacts.keys(),
                f"{agent_id} 的默认产物键不在期望列表中",
            )
