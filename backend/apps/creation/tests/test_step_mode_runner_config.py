# -*- coding: utf-8 -*-
"""分步模式 runner 配置单元测试（新引擎：post-script 步骤走 SkillInvoker）。"""
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from apps.creation.models import Project


class StepModeRunnerTypeUnitTests(SimpleTestCase):
    def test_runner_type_for_node_reads_registry(self):
        from apps.creation import step_mode

        registry = MagicMock()
        registry.runner_type_for_index.return_value = "fusion_score"
        with patch("apps.creation.step_mode.FusionNodeRegistry", return_value=registry):
            self.assertEqual(step_mode.runner_type_for_node(7), "fusion_score")

    def test_runner_path_for_node_reads_registry(self):
        from apps.creation import step_mode

        registry = MagicMock()
        registry.runner_path_for_index.return_value = "apps.creation.step_mode.run_fusion_score_step"
        with patch("apps.creation.step_mode.FusionNodeRegistry", return_value=registry):
            self.assertEqual(
                step_mode.runner_path_for_node(7),
                "apps.creation.step_mode.run_fusion_score_step",
            )

    def test_runner_path_for_node_normalizes_agent_runner(self):
        from apps.creation import step_mode

        registry = MagicMock()
        registry.runner_path_for_index.return_value = "apps.creation.agents.world.run_world_agent"
        registry.runner_type_for_index.return_value = "fusion_node"
        with patch("apps.creation.step_mode.FusionNodeRegistry", return_value=registry):
            self.assertEqual(
                step_mode.runner_path_for_node(2),
                "apps.creation.step_mode.run_orchestrator_step",
            )

    def test_resolve_step_runner_rejects_unsafe_path(self):
        from apps.creation import step_mode

        with patch("apps.creation.step_mode.runner_path_for_node", return_value="os.system"):
            self.assertIsNone(step_mode.resolve_step_runner(7))

    @patch("apps.agent.runtime.agent_for_pipeline_node_index", side_effect=["review", "score"])
    @patch("apps.creation.step_mode.get_skill_invoker")
    def test_run_fusion_step_dispatches_by_runner_type(self, mock_invoker_factory, _mock_agent):
        """新引擎：post-script 步骤走 SkillInvoker → creation.{agent} 技能。"""
        from apps.creation import step_mode

        project = MagicMock()
        project.user_id = 1

        mock_invoker = MagicMock()
        # 模拟 SkillResult：构造两个返回
        success_result = MagicMock()
        success_result.success = True
        success_result.data = {"review_report": {"passed": True}}
        success_result.error = {}
        success_result.skill_id = "creation.review"
        success_result.trace_id = "trace-1"

        success_score = MagicMock()
        success_score.success = True
        success_score.data = {"script_score_report": {"overallScore": 88}}
        success_score.error = {}
        success_score.skill_id = "creation.score"
        success_score.trace_id = "trace-2"

        mock_invoker.invoke.side_effect = [success_result, success_score]
        mock_invoker_factory.return_value = mock_invoker

        self.assertEqual(
            step_mode.run_fusion_step(project, 6, runner_type="fusion_review")["ok"],
            True,
        )
        self.assertEqual(
            step_mode.run_fusion_step(project, 7, runner_type="fusion_score")["ok"],
            True,
        )
        self.assertEqual(mock_invoker.invoke.call_count, 2)


class StepModeRunnerTypeExecutionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(phone="13900005505", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="runner type 测试",
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
    def test_execute_step_uses_fusion_node_runner_type(
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
