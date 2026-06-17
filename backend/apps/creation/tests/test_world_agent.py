# -*- coding: utf-8 -*-
"""工作台 Agent 编排单元测试。"""
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.models import Project
from apps.creation.orchestration.types import AgentResult
from apps.creation.orchestration.world import run_world_agent


def _llm_side_effect(_project, *, agent_id, fusion_node_id, sub_skill_id, upstream, system_hint=""):
    if sub_skill_id == "structure-generator":
        return {
            "sixStagePlan": [
                {
                    "stageIndex": 1,
                    "stageName": "开篇",
                    "startEpisode": 1,
                    "endEpisode": 5,
                    "coreTask": "建立冲突",
                }
            ],
            "rhythmCurve": [],
            "keyReversalPoints": [],
        }
    if sub_skill_id == "world-builder":
        return {
            "worldview": {
                "settingSummary": "现代都市豪门，暗藏身份反转与复仇主线。",
                "timePeriod": "当代",
                "locationType": "urban",
                "rootRules": ["得到多少就要失去多少", "身份秘密一旦公开将引发连锁反应"],
                "coreNouns": [
                    {"term": "裂口", "definition": "痕迹的爆发点", "tier": "mechanism"},
                ],
            }
        }
    if sub_skill_id == "dream-indicators":
        return {
            "dreamIndicators": {
                "fantasyAppeal": {"score": 8, "notes": "幻想感足"},
            }
        }
    return {}


class RunWorldAgentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(phone="13900006601", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="world agent 测试",
            theme="family-revenge",
            episode_count=10,
            status=Project.STATUS_PENDING,
        )
        self.brief = {
            "projectId": str(self.project.id),
            "workingTitle": "world agent 测试",
            "theme": "family-revenge",
            "episodeCount": 10,
            "coreHook": "复仇故事",
        }

    @patch("apps.creation.orchestration.world.persist_execution_trace")
    @patch("apps.creation.orchestration.world._mark_skill_has_content")
    @patch("apps.creation.orchestration.world._run_world_validator")
    @patch("apps.creation.orchestration.world.run_sub_skill_llm", side_effect=_llm_side_effect)
    @patch("apps.creation.orchestration.world.inject_knowledge_upstream")
    @patch("apps.creation.orchestration.world.ensure_brief_seed_enriched")
    @patch("apps.creation.orchestration.world.get_artifact")
    def test_run_world_agent_completes_and_saves_structure_plan(
        self,
        mock_get_artifact,
        _mock_brief_seed,
        mock_inject,
        _mock_llm,
        mock_validate,
        _mock_mark,
        _mock_trace,
    ):
        mock_inject.side_effect = lambda _agent_id, upstream, _project: upstream
        mock_get_artifact.return_value = self.brief
        mock_validate.return_value = {"passed": True, "issues": []}

        saved = {}

        def fake_save_artifact(project, key, payload):
            saved[key] = payload

        with patch("apps.creation.orchestration.world.save_artifact", side_effect=fake_save_artifact):
            result = run_world_agent(self.project, node_index=2)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.agent_id, "world")
        self.assertEqual(result.outputs.get("artifact_key"), "structure_plan")
        plan = saved.get("structure_plan") or {}
        wv = plan.get("worldview") or {}
        self.assertGreaterEqual(len(wv.get("rootRules") or []), 2)
        executed = (result.meta or {}).get("executed_sub_skills") or []
        self.assertIn("structure-generator", executed)
        self.assertIn("world-builder", executed)
        self.assertIn("world-validator", executed)

    @patch("apps.creation.workspace_skill_invoke.invoke_workspace_skill_flat")
    @patch("apps.agent.runtime.agent_for_workspace_index", return_value="world")
    def test_invoke_workspace_agent_routes_node2_to_world_agent(
        self,
        _mock_agent_index,
        mock_flat,
    ):
        from apps.creation.orchestration.types import AgentResult
        from apps.creation.orchestration.workspace_agent import (
            WORKSPACE_AGENT_RUNNERS,
            invoke_workspace_agent,
        )

        mock_flat.return_value = MagicMock(status="error")
        mock_runner = MagicMock(
            return_value=AgentResult(
                status="completed",
                agent_id="world",
                outputs={"artifact_key": "structure_plan"},
                errors=[],
                meta={"executed_sub_skills": ["structure-generator"]},
            )
        )

        with patch.dict(WORKSPACE_AGENT_RUNNERS, {"world": mock_runner}):
            result = invoke_workspace_agent(self.project, 2)

        mock_flat.assert_not_called()
        mock_runner.assert_called_once()
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.agent_id, "world")

    @patch("apps.creation.workspace_skill_invoke.invoke_workspace_skill_flat")
    @patch("apps.agent.runtime.agent_for_workspace_index", return_value="outline")
    def test_invoke_workspace_agent_passes_outline_kwargs(
        self,
        _mock_agent_index,
        mock_flat,
    ):
        from apps.creation.orchestration.workspace_agent import (
            WORKSPACE_AGENT_RUNNERS,
            invoke_workspace_agent,
        )

        mock_flat.return_value = MagicMock(status="error")
        mock_runner = MagicMock(
            return_value=AgentResult(
                status="completed",
                agent_id="outline",
                outputs={"artifact_key": "series_outline"},
                errors=[],
                meta={"outline_mode": "episodes"},
            )
        )

        with patch.dict(WORKSPACE_AGENT_RUNNERS, {"outline": mock_runner}):
            invoke_workspace_agent(
                self.project,
                4,
                script_from=1,
                script_to=3,
                outline_mode="episodes",
            )

        mock_runner.assert_called_once()
        kwargs = mock_runner.call_args.kwargs
        self.assertEqual(kwargs.get("script_from"), 1)
        self.assertEqual(kwargs.get("script_to"), 3)
        self.assertEqual(kwargs.get("outline_mode"), "episodes")
        mock_flat.assert_not_called()
