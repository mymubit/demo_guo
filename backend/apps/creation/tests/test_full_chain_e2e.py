# -*- coding: utf-8 -*-
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentLlmRouteConfig
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.agent_runtime.workspace import build_independent_workspace
from apps.creation.artifact_service import get_artifact
from apps.creation.models import AgentExecutionRun, Project
from apps.skill.models import LlmProvider

User = get_user_model()

CHAIN_AGENTS = [
    "adapt",
    "brief",
    "structure",
    "character",
    "outline",
    "script",
    "review",
    "score",
    "marketing",
]

MOCK_LLM_OUTPUTS = {
    "adapt": {"adaptation_meta": {}, "project_brief": {"status": "confirmed"}},
    "brief": {"project_brief": {"status": "confirmed", "coreIdea": "测试"}},
    "structure": {"structure_plan": {"acts": []}},
    "character": {"character_bible": {"characters": []}},
    "outline": {"series_outline": {"episodes": [{"episodeNumber": 1}]}},
    "script": {"episode_scripts": {"episodes": [{"episodeNumber": 1, "title": "第1集"}]}},
    "review": {"review_report": {"passed": True}},
    "score": {"script_score_report": {"overallScore": 85, "grade": "A"}},
    "marketing": {"marketing_kit": {"titles": ["宣发标题"]}},
}


def _attach_all_routes(provider: LlmProvider) -> None:
    for route in AgentLlmRouteConfig.objects.all():
        route.llm_provider = provider
        route.save(update_fields=["llm_provider"])


class FullChainE2ETests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        provider = LlmProvider.objects.create(
            name="full-chain-provider",
            model_name="gpt-test",
            is_enabled=True,
            is_active=True,
        )
        _attach_all_routes(provider)
        self.user = User.objects.create_user(phone="13900008930", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="全链路测试",
            theme="overbearing-ceo",
            core_idea="全链路",
            episode_count=10,
            format_variant="B",
            novel_text="小说正文" * 50,
            creation_entry="novel-adaptation",
            fusion_status=Project.FUSION_DRAFT,
        )

    def _mock_side_effect(self, agent_id: str):
        def _side_effect(**kwargs):
            payload = MOCK_LLM_OUTPUTS[agent_id]
            return json.dumps(payload, ensure_ascii=False)

        return _side_effect

    @patch("apps.creation.agent_runtime.independent_service.LlmService.chat_completion")
    def test_full_chain_runs_all_agents_and_enables_download_share(self, mock_chat):
        for agent_id in CHAIN_AGENTS:
            mock_chat.side_effect = self._mock_side_effect(agent_id)
            result = IndependentAgentService.enqueue_run(self.project, self.user, agent_id, {})
            self.assertTrue(result.should_enqueue, f"{agent_id} enqueue 失败")
            run = IndependentAgentService.execute_run(result.run)
            self.assertEqual(
                run.status,
                AgentExecutionRun.STATUS_COMPLETED,
                f"{agent_id} 执行失败: {run.error_message}",
            )
            self.project.refresh_from_db()

        self.assertIsNotNone(get_artifact(self.project, "episode_scripts"))
        self.assertIsNotNone(get_artifact(self.project, "marketing_kit"))
        self.assertEqual(self.project.execution_status, Project.STATUS_COMPLETED)

        workspace = build_independent_workspace(self.project)
        self.assertTrue(workspace["project"]["can_download"])
        self.assertTrue(workspace["project"]["can_share"])

    @patch("apps.creation.agent_runtime.independent_service.LlmService.chat_completion")
    def test_adapt_build_input_contains_novel_text(self, mock_chat):
        mock_chat.return_value = json.dumps(MOCK_LLM_OUTPUTS["adapt"], ensure_ascii=False)
        agent = AgentDefinitionService.get_runnable("adapt")
        payload = IndependentAgentService.build_agent_input(self.project, agent, {})
        self.assertEqual(payload["project"]["novel_text"], self.project.novel_text)


class FullChainPortalApiTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        provider = LlmProvider.objects.create(
            name="portal-chain-provider",
            model_name="gpt-test",
            is_enabled=True,
            is_active=True,
        )
        _attach_all_routes(provider)
        self.user = User.objects.create_user(phone="13900008931", password="test-pass-123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(
            user=self.user,
            title="Portal 链路",
            theme="sweet-pet",
            core_idea="测试",
            episode_count=8,
            format_variant="B",
            fusion_status=Project.FUSION_READY,
        )
        from apps.creation.artifact_service import save_artifact

        save_artifact(
            self.project,
            "episode_scripts",
            {"episodes": [{"episodeNumber": 1, "title": "第1集"}]},
        )

    def test_workspace_api_contract(self):
        resp = self.client.get(f"/api/creation/projects/{self.project.id}/workspace/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertIn("project", data)
        self.assertIn("agents", data)
        self.assertTrue(data["project"]["can_download"])

    def test_download_requires_episode_scripts(self):
        resp = self.client.get(f"/api/creation/download/{self.project.id}/?format=md")
        self.assertEqual(resp.status_code, 200)

    def test_share_requires_completed_status(self):
        resp = self.client.post(
            f"/api/creation/share/{self.project.id}/",
            {"allow_download": False},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["code"], 0)
        self.assertIn("share_url", resp.json()["data"])
