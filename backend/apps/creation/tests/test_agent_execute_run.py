# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentLlmRouteConfig
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.artifact_service import save_artifact
from apps.creation.models import AgentExecutionRun, Project
from apps.creation.tasks import run_independent_agent
from apps.skill.models import LlmProvider

User = get_user_model()


def _attach_test_llm_provider(agent_id: str) -> LlmProvider:
    provider = LlmProvider.objects.create(
        name=f"test-exec-{agent_id}",
        model_name="gpt-test",
        is_enabled=True,
    )
    route = AgentLlmRouteConfig.objects.get(route_key=agent_id)
    route.llm_provider = provider
    route.save(update_fields=["llm_provider"])
    return provider


class AgentExecuteRunTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        _attach_test_llm_provider("brief")
        self.user = User.objects.create_user(phone="13900008801", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="exec-test",
            theme="overbearing-ceo",
            core_idea="测试 execute_run",
            episode_count=20,
            format_variant="B",
        )
        save_artifact(
            self.project,
            "project_brief",
            {"status": "confirmed", "coreIdea": "测试"},
        )
        self.run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="brief",
            status=AgentExecutionRun.STATUS_RUNNING,
            run_params={},
            input_snapshot={"project": {}, "artifacts": {}, "params": {}},
        )

    @patch("apps.creation.agent_runtime.independent_service.LlmService.chat_completion")
    def test_execute_run_persists_output_and_updates_project_status(self, mock_chat):
        mock_chat.return_value = '{"project_brief": {"status": "confirmed", "coreIdea": "AI 输出"}}'
        result = IndependentAgentService.execute_run(self.run)
        self.project.refresh_from_db()
        self.assertEqual(result.status, AgentExecutionRun.STATUS_COMPLETED)
        self.assertEqual(self.project.status, Project.STATUS_PENDING)
        self.assertIn(self.project.fusion_status, {Project.FUSION_DRAFT, Project.FUSION_PLANNING})

    @patch("apps.creation.agent_runtime.independent_service.LlmService.chat_completion")
    def test_run_independent_agent_task_invokes_execute(self, mock_chat):
        mock_chat.return_value = '{"project_brief": {"status": "confirmed", "coreIdea": "task 输出"}}'
        payload = run_independent_agent.call(
            str(self.project.id),
            "brief",
            {},
            run_id=str(self.run.id),
        )
        self.run.refresh_from_db()
        self.assertEqual(self.run.status, AgentExecutionRun.STATUS_COMPLETED)
        self.assertIn("status", payload)

    @patch("apps.creation.agent_runtime.independent_service.LlmService.chat_completion")
    def test_execute_run_marks_failed_on_llm_error(self, mock_chat):
        mock_chat.side_effect = RuntimeError("LLM 不可用")
        IndependentAgentService.execute_run(self.run)
        self.run.refresh_from_db()
        self.assertEqual(self.run.status, AgentExecutionRun.STATUS_FAILED)
        self.assertIn("LLM", self.run.error_message)


class ProjectStatusSyncTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.user = User.objects.create_user(phone="13900008802", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="status-sync",
            theme="overbearing-ceo",
            core_idea="状态同步",
            episode_count=20,
            format_variant="B",
            fusion_status=Project.FUSION_DRAFT,
            status=Project.STATUS_PENDING,
        )

    def test_update_project_status_sets_completed_when_scripts_exist(self):
        save_artifact(
            self.project,
            "episode_scripts",
            {"episodes": [{"episodeNumber": 1, "title": "第1集"}]},
        )
        IndependentAgentService.update_project_status(self.project)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_COMPLETED)
        self.assertEqual(self.project.fusion_status, Project.FUSION_READY)
        self.assertEqual(self.project.progress_percent, 100)

    def test_enqueue_sets_running_status_not_reverted_to_pending(self):
        _attach_test_llm_provider("brief")
        save_artifact(self.project, "project_brief", {"status": "confirmed"})
        result = IndependentAgentService.enqueue_run(self.project, self.user, "brief", {})
        self.project.refresh_from_db()
        self.assertTrue(result.created_new_run)
        self.assertEqual(self.project.status, Project.STATUS_RUNNING)
        self.assertEqual(self.project.fusion_status, Project.FUSION_WRITING)
