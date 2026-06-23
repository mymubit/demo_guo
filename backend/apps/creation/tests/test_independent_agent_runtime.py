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

from apps.creation.tests.test_helpers import grant_test_coins

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
        _attach_test_llm_provider("drama.topic-planner")
        self.user = User.objects.create_user(phone="13900007701", password="test-pass-123")
        grant_test_coins(self.user)
        self.project = Project.objects.create(
            user=self.user,
            title="enqueue-test",
            theme="overbearing-ceo",
            core_idea="??????",
            episode_count=20,
            format_variant="B",
        )

    def test_enqueue_returns_existing_running_without_creating_duplicate(self):
        first = IndependentAgentService.enqueue_run(self.project, self.user, "drama.topic-planner", {})
        self.assertTrue(first.created_new_run)
        self.assertTrue(first.should_enqueue)

        second = IndependentAgentService.enqueue_run(self.project, self.user, "drama.topic-planner", {})
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
        url = f"/api/creation/projects/{self.project.id}/agents/drama.topic-planner/run/"

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
            core_idea="?? merge ??",
            episode_count=20,
            format_variant="B",
        )
        save_artifact(
            self.project,
            "episode_scripts",
            {
                "episodes": [
                    {"episodeNumber": 1, "title": "?1?"},
                    {"episodeNumber": 2, "title": "?2?"},
                ]
            },
        )
        self.agent = AgentDefinitionService.get_runnable("drama.script-writer")
        self.run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="drama.script-writer",
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
                        {"episodeNumber": 2, "title": "??2?"},
                        {"episodeNumber": 3, "title": "?3?"},
                        {"episodeNumber": 99, "title": "????"},
                    ]
                }
            },
            prompt_version="v1",
        )
        merged = get_artifact(self.project, "episode_scripts") or {}
        by_num = {ep["episodeNumber"]: ep["title"] for ep in merged.get("episodes") or []}
        self.assertEqual(by_num[1], "?1?")
        self.assertEqual(by_num[2], "??2?")
        self.assertEqual(by_num[3], "?3?")
        self.assertNotIn(99, by_num)

    def test_persist_merge_narrative_plan_keeps_previous_batches(self):
        save_artifact(
            self.project,
            "narrative_plan",
            {
                "target_episode_range": "E001-E005",
                "episode_narrative_designs": [
                    {"episode_id": "E001", "narrative_focus": "第一集"},
                    {"episode_id": "E005", "narrative_focus": "第五集"},
                ],
            },
        )
        agent = AgentDefinitionService.get_runnable("drama.narrative-engineer")
        self.run.status = AgentExecutionRun.STATUS_COMPLETED
        self.run.save(update_fields=["status"])
        run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="drama.narrative-engineer",
            status=AgentExecutionRun.STATUS_COMPLETED,
            batch_from=6,
            batch_to=10,
            overwrite_mode="merge",
            run_params={"episode_start": 6, "episode_end": 10, "episode_range": "6-10"},
        )
        IndependentAgentService.persist_agent_output(
            self.project,
            agent,
            run,
            {
                "narrative_plan": {
                    "target_episode_range": "E006-E010",
                    "narrative_core_objective": "6-10集强化",
                    "episode_narrative_designs": [
                        {"episode_id": "E006", "narrative_focus": "第六集"},
                        {"episode_id": "E010", "narrative_focus": "第十集"},
                    ],
                }
            },
            prompt_version="v1",
        )
        merged = get_artifact(self.project, "narrative_plan") or {}
        ids = [item["episode_id"] for item in merged.get("episode_narrative_designs") or []]
        self.assertEqual(ids, ["E001", "E005", "E006", "E010"])
        self.assertEqual(merged.get("target_episode_range"), "E001-E010")

    def test_resolve_episode_bounds_reads_episode_start_end(self):
        from_ep, to_ep = IndependentAgentService._resolve_episode_bounds(
            {"episode_start": 6, "episode_end": 10, "episode_range": "6-10"}
        )
        self.assertEqual((from_ep, to_ep), (6, 10))


class IndependentAgentTemplateTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.agent = AgentDefinitionService.get_runnable("drama.topic-planner")

    def test_render_template_supports_dot_path_variables(self):
        context = {
            "agent": self.agent,
            "input": {
                "project": {"core_idea": "????", "theme": "overbearing-ceo"},
                "artifacts": {"project_brief": {"status": "confirmed"}},
                "params": {"episode_from": 1},
            },
            "knowledge": [],
        }
        rendered = IndependentAgentService._render_template(
            "idea={{ project.core_idea }} brief={{ artifacts.project_brief }} from={{ params.episode_from }}",
            context,
        )
        self.assertIn("????", rendered)
        self.assertIn('"status": "confirmed"', rendered)
        self.assertIn("from=1", rendered)


class IndependentAgentPreviewTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        _attach_test_llm_provider("drama.topic-planner")
        self.user = User.objects.create_user(phone="13900007704", password="test-pass-123")
        grant_test_coins(self.user)
        self.project = Project.objects.create(
            user=self.user,
            title="preview-test",
            theme="overbearing-ceo",
            core_idea="????",
            episode_count=20,
            format_variant="B",
        )

    def test_preview_run_does_not_create_execution_run(self):
        before = AgentExecutionRun.objects.filter(project=self.project).count()
        preview = IndependentAgentService.preview_run(self.project, "drama.topic-planner", {})
        after = AgentExecutionRun.objects.filter(project=self.project).count()
        self.assertEqual(before, after)
        self.assertIn("estimated_prompt_tokens", preview)
        self.assertIn("within_limit", preview)

    def test_estimate_api_returns_tokens(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        res = client.post(
            f"/api/creation/projects/{self.project.id}/agents/drama.topic-planner/estimate/",
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
            "core_idea": "????????? pipeline ??",
            "episode_count": 20,
            "format_variant": "B",
            "target_platform": "douyin",
            "budget_level": "medium",
            "pipeline_mode": Project.MODE_WORKSPACE,
        }

    @patch("apps.billing.services.BillingService.charge")
    @patch("apps.billing.services.BillingService.ensure_can_create")
    @patch("apps.creation.services.submission.MembershipService.get_current_membership", return_value=None)
    @patch("dj_queue.api.enqueue_on_commit")
    def test_submit_does_not_enqueue_legacy_pipeline(
        self,
        mock_enqueue,
        _mock_membership,
        _mock_can_create,
        _mock_charge,
    ):
        project, _ = submit(self.user, self._payload())
        mock_enqueue.assert_not_called()
        self.assertEqual(project.execution_status, Project.STATUS_PENDING)


class IndependentAgentOutputValidationTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.script_writer_agent = AgentDefinitionService.get_runnable("drama.script-writer")
        self.script_reviewer_agent = AgentDefinitionService.get_runnable("drama.script-reviewer")

    def test_validate_output_rejects_episode_without_number(self):
        with self.assertRaises(Exception) as ctx:
            IndependentAgentService.validate_output(
                self.script_writer_agent,
                {
                    "episode_scripts": {
                        "episodes": [{"title": "???"}],
                    }
                },
            )
        self.assertIn("episodeNumber", str(ctx.exception))

    def test_validate_output_accepts_valid_episode_scripts(self):
        result = IndependentAgentService.validate_output(
            self.script_writer_agent,
            {
                "episode_scripts": {
                    "episodes": [{"episodeNumber": 1, "title": "?1?"}],
                }
            },
        )
        self.assertIn("episode_scripts", result)

    def test_validate_output_rejects_review_report_without_passed(self):
        with self.assertRaises(Exception) as ctx:
            IndependentAgentService.validate_output(
                self.script_reviewer_agent,
                {"review_report": {"issues": []}},
            )
        self.assertIn("passed", str(ctx.exception))


class ReportArtifactEditorViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900007705", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="report-view-test",
            theme="overbearing-ceo",
            core_idea="??????",
            episode_count=20,
            format_variant="B",
        )

    def test_build_artifact_editor_view_routes_review_report(self):
        from apps.creation.workspace.workspace_editor import build_artifact_editor_view

        save_artifact(
            self.project,
            "review_report",
            {"agentId": "drama.script-reviewer", "passed": True, "issues": []},
        )
        view = build_artifact_editor_view(self.project, "review_report")
        self.assertEqual(view["mode"], "review_report")
        self.assertTrue(view["payload"]["passed"])

    def test_build_artifact_editor_view_routes_script_score_report(self):
        from apps.creation.workspace.workspace_editor import build_artifact_editor_view

        save_artifact(
            self.project,
            "script_score_report",
            {"agentId": "score", "overallScore": 88, "grade": "A"},
        )
        view = build_artifact_editor_view(self.project, "script_score_report")
        self.assertEqual(view["mode"], "score_report")
        self.assertEqual(view["payload"]["overallScore"], 88)
