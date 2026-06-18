# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import AgentLlmRouteConfig
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import AgentExecutionRun, Project
from apps.creation.services.submission import submit
from apps.skill.models import LlmProvider
from apps.workflow.execution_models import WorkflowInstance

User = get_user_model()


def _attach_test_llm_provider(agent_id: str) -> LlmProvider:
    provider = LlmProvider.objects.create(
        name=f"test-{agent_id}",
        model_name="gpt-test",
        is_enabled=True,
    )
    route = AgentLlmRouteConfig.objects.get(route_key=agent_id)
    route.llm_provider = provider
    route.save(update_fields=["llm_provider"])
    return provider


class IndependentAgentEnqueueTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        _attach_test_llm_provider("brief")
        self.user = User.objects.create_user(phone="13900007701", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="enqueue-test",
            theme="overbearing-ceo",
            core_idea="测试并发入队",
            episode_count=20,
            format_variant="B",
            status=Project.STATUS_PENDING,
        )

    def test_enqueue_returns_existing_running_without_creating_duplicate(self):
        first = IndependentAgentService.enqueue_run(self.project, self.user, "brief", {})
        self.assertTrue(first.created_new_run)
        self.assertTrue(first.should_enqueue)

        second = IndependentAgentService.enqueue_run(self.project, self.user, "brief", {})
        self.assertFalse(second.created_new_run)
        self.assertFalse(second.should_enqueue)
        self.assertEqual(second.run.id, first.run.id)
        self.assertEqual(
            AgentExecutionRun.objects.filter(project=self.project, status=AgentExecutionRun.STATUS_RUNNING).count(),
            1,
        )

    @patch("dj_queue.api.enqueue_on_commit")
    def test_run_api_skips_enqueue_when_run_already_running(self, mock_enqueue):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = f"/api/creation/projects/{self.project.id}/agents/brief/run/"

        first = client.post(url, {"params": {}}, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["code"], 0)
        self.assertTrue(first.data["data"]["created_new_run"])
        self.assertEqual(mock_enqueue.call_count, 1)

        second = client.post(url, {"params": {}}, format="json")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["code"], 0)
        self.assertFalse(second.data["data"]["created_new_run"])
        self.assertTrue(second.data["data"]["already_running"])
        self.assertEqual(mock_enqueue.call_count, 1)


class IndependentAgentMergePersistTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.user = User.objects.create_user(phone="13900007702", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="merge-test",
            theme="overbearing-ceo",
            core_idea="测试 merge 写入",
            episode_count=20,
            format_variant="B",
            status=Project.STATUS_PENDING,
        )
        save_artifact(
            self.project,
            "episode_scripts",
            {
                "episodes": [
                    {"episodeNumber": 1, "title": "旧第1集"},
                    {"episodeNumber": 2, "title": "旧第2集"},
                ]
            },
        )
        self.agent = AgentDefinitionService.get_runnable("script")
        self.run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="script",
            status=AgentExecutionRun.STATUS_RUNNING,
            batch_from=2,
            batch_to=3,
            overwrite_mode="merge",
            run_params={"episode_from": 2, "episode_to": 3},
        )

    def test_persist_merge_updates_only_requested_episode_range(self):
        IndependentAgentService.persist_agent_output(
            self.project,
            self.agent,
            self.run,
            {
                "episode_scripts": {
                    "episodes": [
                        {"episodeNumber": 2, "title": "新第2集"},
                        {"episodeNumber": 3, "title": "新第3集"},
                        {"episodeNumber": 99, "title": "越界集"},
                    ]
                }
            },
            prompt_version="v1",
        )
        merged = get_artifact(self.project, "episode_scripts") or {}
        by_num = {ep["episodeNumber"]: ep["title"] for ep in merged.get("episodes") or []}
        self.assertEqual(by_num[1], "旧第1集")
        self.assertEqual(by_num[2], "新第2集")
        self.assertEqual(by_num[3], "新第3集")
        self.assertNotIn(99, by_num)


class IndependentAgentTemplateTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.agent = AgentDefinitionService.get_runnable("brief")

    def test_render_template_supports_dot_path_variables(self):
        context = {
            "agent": self.agent,
            "input": {
                "project": {"core_idea": "女主逆袭", "theme": "overbearing-ceo"},
                "artifacts": {"project_brief": {"status": "confirmed"}},
                "params": {"episode_from": 1},
            },
            "knowledge": [],
        }
        rendered = IndependentAgentService._render_template(
            "idea={{ project.core_idea }} brief={{ artifacts.project_brief }} from={{ params.episode_from }}",
            context,
        )
        self.assertIn("女主逆袭", rendered)
        self.assertIn('"status": "confirmed"', rendered)
        self.assertIn("from=1", rendered)


class IndependentAgentPreviewTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        _attach_test_llm_provider("brief")
        self.user = User.objects.create_user(phone="13900007704", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="preview-test",
            theme="overbearing-ceo",
            core_idea="测试预估",
            episode_count=20,
            format_variant="B",
            status=Project.STATUS_PENDING,
        )

    def test_preview_run_does_not_create_execution_run(self):
        before = AgentExecutionRun.objects.filter(project=self.project).count()
        preview = IndependentAgentService.preview_run(self.project, "brief", {})
        after = AgentExecutionRun.objects.filter(project=self.project).count()
        self.assertEqual(before, after)
        self.assertIn("estimated_prompt_tokens", preview)
        self.assertIn("within_limit", preview)

    def test_estimate_api_returns_tokens(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        res = client.post(
            f"/api/creation/projects/{self.project.id}/agents/brief/estimate/",
            {"params": {}},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("code"), 0)
        self.assertIn("estimated_prompt_tokens", body.get("data") or {})


class CreationSubmitLegacyIsolationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900007703", password="test-pass-123")

    def _payload(self):
        return {
            "theme": "overbearing-ceo",
            "core_idea": "一个被误解的女主重回豪门，在权力与情感夹缝中反击。",
            "episode_count": 20,
            "format_variant": "B",
            "target_platform": "douyin",
            "budget_level": "medium",
            "pipeline_mode": Project.MODE_WORKSPACE,
        }

    @patch("apps.billing.services.BillingService.charge")
    @patch("apps.billing.services.BillingService.ensure_can_create")
    @patch("apps.creation.services.submission.MembershipService.get_current_membership", return_value=None)
    @patch("apps.creation.tasks.run_creation_pipeline")
    @patch("dj_queue.api.enqueue_on_commit")
    def test_submit_does_not_enqueue_legacy_pipeline(
        self,
        mock_enqueue,
        mock_pipeline,
        _mock_membership,
        _mock_can_create,
        _mock_charge,
    ):
        project, _ = submit(self.user, self._payload())
        mock_pipeline.delay.assert_not_called()
        mock_pipeline.apply_async.assert_not_called()
        mock_enqueue.assert_not_called()
        self.assertEqual(WorkflowInstance.objects.filter(project_id=project.id).count(), 0)
        self.assertEqual(project.total_nodes, 0)
        self.assertEqual(project.status, Project.STATUS_PENDING)
