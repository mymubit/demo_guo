# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from apps.creation.models import Project


class StepModeRunnerTypeUnitTests(SimpleTestCase):
    def test_runner_type_for_node_reads_registry_for_main_chain(self):
        from apps.creation import step_mode

        registry = MagicMock()
        registry.runner_type_for_index.return_value = "fusion_node"
        with patch("apps.creation.step_mode.FusionNodeRegistry", return_value=registry):
            self.assertEqual(step_mode.runner_type_for_node(5), "fusion_node")

    def test_runner_path_for_node_normalizes_main_chain_runner(self):
        from apps.creation import step_mode

        registry = MagicMock()
        registry.runner_path_for_index.return_value = "apps.creation.agents.script.run_script_agent"
        registry.runner_type_for_index.return_value = "fusion_node"
        with patch("apps.creation.step_mode.FusionNodeRegistry", return_value=registry):
            self.assertEqual(
                step_mode.runner_path_for_node(5),
                "apps.creation.step_mode.run_orchestrator_step",
            )

    def test_resolve_step_runner_rejects_unsafe_path(self):
        from apps.creation import step_mode

        with patch("apps.creation.step_mode.runner_path_for_node", return_value="os.system"):
            self.assertIsNone(step_mode.resolve_step_runner(5))

    def test_post_runner_entry_is_removed(self):
        from apps.creation import step_mode

        with self.assertRaisesMessage(ValueError, "post-processing runners have been removed"):
            step_mode.run_fusion_step(MagicMock(), 6, runner_type="review")


class StepModeRunnerTypeExecutionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(phone="13900005505", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="runner type test",
            theme="sweet-pet",
            episode_count=2,
            pipeline_mode=Project.MODE_STEP,
            status=Project.STATUS_PENDING,
        )

    @patch("apps.creation.step_mode.node_requires_confirm", return_value=False)
    @patch("apps.creation.step_mode.charge_node_success")
    @patch("apps.creation.step_mode.run_orchestrator_step", return_value={"status": "completed"})
    @patch("apps.creation.step_mode.runner_path_for_node", return_value="apps.creation.step_mode.run_orchestrator_step")
    @patch("apps.creation.step_mode.runner_type_for_node", return_value="fusion_node")
    @patch("apps.workflow.services.pipeline_service.WorkflowPipelineService.creation_max_node_index", return_value=1)
    @patch("apps.workflow.services.pipeline_service.WorkflowPipelineService.is_node_enabled", return_value=True)
    def test_execute_step_uses_main_chain_runner(
        self,
        _mock_enabled,
        _mock_max,
        _mock_runner_type,
        _mock_runner_path,
        mock_orchestrator,
        _mock_charge,
        _mock_confirm,
    ):
        from apps.creation.step_mode import execute_step

        result = execute_step(self.project, 1)

        self.assertEqual(result["status"], "completed")
        mock_orchestrator.assert_called_once()
