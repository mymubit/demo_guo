# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.orchestration.orchestrator import AgentOrchestrator
from apps.creation.artifact_service import save_artifact
from apps.creation.models import Project
from apps.creation.post_script_summary import build_post_script_summary
from apps.creation.tasks import run_agent_post_chain

User = get_user_model()


class PostScriptOrchestratorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900004403", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="后处理测试",
            theme="sweet-pet",
            episode_count=2,
            pipeline_mode=Project.MODE_WORKSPACE,
            status=Project.STATUS_PENDING,
        )
        save_artifact(
            self.project,
            "episode_scripts",
            {
                "episodes": [
                    {"episodeNumber": 1, "title": "第1集", "full_script_text": "剧本1"},
                    {"episodeNumber": 2, "title": "第2集", "full_script_text": "剧本2"},
                ]
            },
        )

    def test_scripts_fully_generated(self):
        orch = AgentOrchestrator(self.project)
        self.assertTrue(orch.scripts_fully_generated())

    def test_scripts_not_fully_generated(self):
        save_artifact(
            self.project,
            "episode_scripts",
            {"episodes": [{"episodeNumber": 1, "title": "第1集"}]},
        )
        orch = AgentOrchestrator(self.project)
        self.assertFalse(orch.scripts_fully_generated())

    @patch("apps.creation.orchestration.orchestrator.resolve_agent_runner")
    @patch(
        "apps.creation.orchestration.orchestrator.post_script_effective_chain",
        return_value=["review", "polish", "review", "score"],
    )
    @patch("apps.creation.orchestration.marketing.run_marketing_agent")
    @patch("apps.creation.orchestration.score.run_score_agent")
    @patch("apps.creation.orchestration.polish.run_polish_agent")
    @patch("apps.creation.orchestration.review.run_review_agent")
    def test_run_post_script_chain_mock(
        self,
        mock_review,
        mock_polish,
        mock_score,
        mock_marketing,
        _mock_chain,
        mock_resolve_runner,
    ):
        from apps.creation.orchestration.base import AgentResult

        mock_review.return_value = AgentResult(
            agent_id="review",
            status="completed",
            outputs={"review_report": {"passed": True, "issues": []}},
        )
        mock_polish.return_value = AgentResult(
            agent_id="polish",
            status="completed",
            outputs={"polish_log": {"suggestions": [{"advice": "节奏略慢"}]}},
        )
        mock_score.return_value = AgentResult(
            agent_id="score",
            status="completed",
            outputs={"script_score_report": {"overallScore": 88}},
        )
        mock_marketing.return_value = AgentResult(agent_id="marketing", status="completed")
        mock_resolve_runner.side_effect = lambda agent_id: {
            "review": mock_review,
            "polish": mock_polish,
            "score": mock_score,
            "marketing": mock_marketing,
        }.get(agent_id)

        orch = AgentOrchestrator(self.project)
        out = orch.run_post_script_chain()
        self.assertEqual(out["status"], "completed")
        self.assertIn("review", out["chain"])

    @patch("apps.creation.orchestration.orchestrator.AgentOrchestrator")
    def test_run_agent_post_chain_marks_completed(self, mock_orch_cls):
        mock_orch = MagicMock()
        mock_orch.scripts_fully_generated.return_value = True
        mock_orch.run_post_script_chain.return_value = {"status": "completed", "chain": ["review"]}
        mock_orch_cls.return_value = mock_orch

        result = run_agent_post_chain.call(str(self.project.id))
        self.assertEqual(result["status"], "done")
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_COMPLETED)

    def test_post_script_summary_chain_includes_marketing(self):
        summary = build_post_script_summary(self.project)
        chain = summary.get("chain") or []
        self.assertIn("review", chain)
        self.assertIn("marketing", chain)
