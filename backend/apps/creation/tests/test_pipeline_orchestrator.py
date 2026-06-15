# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from apps.creation.orchestration.orchestrator import (
    AgentOrchestrator,
    agent_result_to_fusion_post_step,
    agent_result_to_workspace_step,
    run_pipeline_step_by_index,
)
from apps.creation.orchestration.types import AgentResult, WorkspaceInvokeOptions
from apps.creation.models import Project


class PipelineOrchestratorUnitTests(SimpleTestCase):
    def test_agent_result_to_workspace_step_error(self):
        result = AgentResult(agent_id="world", status="error", errors=["依赖缺失"])
        out = agent_result_to_workspace_step(result, 2)
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["errors"], ["依赖缺失"])

    def test_agent_result_to_workspace_step_completed(self):
        result = AgentResult(
            agent_id="world",
            status="completed",
            outputs={"artifact_key": "structure_plan"},
        )
        out = agent_result_to_workspace_step(result, 2)
        self.assertEqual(out["status"], "completed")
        self.assertEqual(out["artifact_key"], "structure_plan")
        self.assertEqual(out["agent_id"], "world")

    def test_agent_result_to_fusion_post_step_preserves_ok(self):
        result = AgentResult(
            agent_id="review",
            status="completed",
            meta={"fusion": {"ok": False, "skipped": False, "error": "gate 未通过"}},
        )
        out = agent_result_to_fusion_post_step(result, 6)
        self.assertEqual(out["status"], "completed")
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "gate 未通过")

    @patch("apps.creation.orchestration.orchestrator.AgentOrchestrator.invoke_workspace")
    @patch("apps.creation.orchestration.orchestrator.agent_for_pipeline_node_index", return_value="brief")
    @patch("apps.creation.orchestration.orchestrator._runner_type_for_pipeline_index", return_value="fusion_node")
    def test_invoke_pipeline_step_dispatches_workspace_agent(
        self, _mock_runner_type, _mock_agent, mock_invoke
    ):
        project = MagicMock()
        mock_invoke.return_value = AgentResult(
            agent_id="brief",
            status="completed",
            outputs={"artifact_key": "project_brief"},
        )
        out = AgentOrchestrator(project).invoke_pipeline_step(1)
        self.assertEqual(out["status"], "completed")
        self.assertEqual(out["agent_id"], "brief")
        mock_invoke.assert_called_once()
        opts = mock_invoke.call_args[0][0]
        self.assertIsInstance(opts, WorkspaceInvokeOptions)
        self.assertEqual(opts.node_index, 1)

    @patch("apps.creation.orchestration.orchestrator.AgentOrchestrator.invoke")
    @patch("apps.creation.orchestration.orchestrator.agent_for_pipeline_node_index", return_value="review")
    @patch("apps.creation.orchestration.orchestrator._runner_type_for_pipeline_index", return_value="fusion_review")
    def test_invoke_pipeline_step_dispatches_review_agent(self, _mock_runner_type, _mock_agent, mock_invoke):
        project = MagicMock()
        mock_invoke.return_value = AgentResult(
            agent_id="review",
            status="completed",
            meta={"fusion": {"ok": True, "skipped": False}},
        )
        out = AgentOrchestrator(project).invoke_pipeline_step(6)
        self.assertEqual(out["status"], "completed")
        self.assertTrue(out["ok"])
        mock_invoke.assert_called_once_with("review")


class StepModeOrchestratorIntegrationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(phone="13900005506", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="pipeline orchestrator 测试",
            theme="sweet-pet",
            episode_count=2,
            pipeline_mode=Project.MODE_STEP,
            status=Project.STATUS_PENDING,
        )

    @patch("apps.creation.orchestration.orchestrator.run_pipeline_step_by_index", return_value={"status": "completed"})
    @patch("apps.creation.step_mode.runner_path_for_node", return_value="apps.creation.step_mode.run_orchestrator_step")
    @patch("apps.creation.step_mode.runner_type_for_node", return_value="fusion_node")
    @patch("apps.workflow.services.pipeline_service.WorkflowPipelineService.creation_max_node_index", return_value=1)
    @patch("apps.workflow.services.pipeline_service.WorkflowPipelineService.is_node_enabled", return_value=True)
    @patch("apps.creation.step_mode.node_requires_confirm", return_value=False)
    @patch("apps.creation.step_mode.charge_node_success")
    def test_execute_step_routes_through_pipeline_orchestrator(
        self,
        _mock_charge,
        _mock_confirm,
        _mock_enabled,
        _mock_max,
        _mock_runner_type,
        _mock_runner_path,
        mock_pipeline_step,
    ):
        from apps.creation.step_mode import execute_step

        result = execute_step(self.project, 1)
        self.assertEqual(result["status"], "completed")
        mock_pipeline_step.assert_called_once_with(self.project, 1)
