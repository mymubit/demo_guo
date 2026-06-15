# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from apps.creation.orchestration.sub_skill_runner import (
    cli_brief_enrich,
    cli_compliance_check,
    cli_episode_gate,
    cli_gate_full,
    cli_marketing_kit,
    cli_plan_validate,
    cli_score_deep,
    cli_score_quick,
    cli_verify_creation_brief,
    cli_verify_creation_setting,
    cli_world_validate,
    resolve_registry_script_path,
    run_cli_sub_skill,
    unwrap_fusion_cli_result,
)


class SubSkillCliTests(SimpleTestCase):
    def test_unwrap_fusion_cli_result_reads_inner_json(self):
        outer = {
            "ok": False,
            "exit_code": 1,
            "json": {
                "passed": False,
                "issues": ["worldview.settingSummary 须 ≥5 字"],
            },
        }
        inner = unwrap_fusion_cli_result(outer)
        self.assertFalse(inner["passed"])
        self.assertEqual(len(inner["issues"]), 1)

    def test_run_cli_sub_skill_rejects_non_cli(self):
        runner = MagicMock()
        with self.assertRaises(ValueError):
            run_cli_sub_skill(runner, "brief", "brief-form-collector", [])

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_brief_enrich_builds_args(self, mock_run):
        mock_run.return_value = {"ok": True}
        runner = MagicMock()
        cli_brief_enrich(runner, "/tmp/in.json", output_path="/tmp/out.json")
        args = mock_run.call_args[0][3]
        self.assertTrue(any(a.startswith("--input=") for a in args))
        self.assertTrue(any(a.startswith("--output=") for a in args))

    def test_brief_enrich_unwraps_project_brief(self):
        from apps.creation.orchestration.sub_skill_orchestrator import SubSkillOrchestrator

        orch = MagicMock()
        orch.runner = MagicMock()
        orch.project = MagicMock()
        orch.project.id.hex = "abc"
        orch.work_dir = MagicMock()
        orch.work_dir.__truediv__ = lambda self, x: MagicMock()
        in_path = MagicMock()
        out_path = MagicMock()
        out_path.is_file.return_value = False
        in_path.write_text = MagicMock()
        out_path.write_text = MagicMock()

        with patch("apps.creation.orchestration.sub_skill_orchestrator.cli_brief_enrich") as mock_cli:
            mock_cli.return_value = {
                "ok": True,
                "json": {
                    "projectBrief": {"coreHook": "测试梗概足够长", "theme": "sweet-pet"},
                },
            }
            with patch.object(orch.work_dir, "__truediv__", side_effect=[in_path, out_path]):
                sub = SubSkillOrchestrator(orch, "brief")
                out = sub.run_brief_enrich_cli({"theme": "sweet-pet"}, in_path=in_path, out_path=out_path)
        self.assertEqual(out.get("coreHook"), "测试梗概足够长")

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_world_validate_no_strict(self, mock_run):
        mock_run.return_value = {"ok": True}
        cli_world_validate(MagicMock(), "/tmp/structure.json", strict=False)
        args = mock_run.call_args[0][3]
        self.assertIn("--no-strict", args)

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_plan_validate_episodes(self, mock_run):
        mock_run.return_value = {"ok": True}
        cli_plan_validate(MagicMock(), "/tmp/outline.json", episodes=80)
        args = mock_run.call_args[0][3]
        self.assertIn("--episodes=80", args)

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_episode_gate(self, mock_run):
        mock_run.return_value = {"ok": True, "json": {"passed": True}}
        cli_episode_gate(MagicMock(), "/tmp/ep1.md", episode=1, strict=False)
        args = mock_run.call_args[0][3]
        self.assertIn("--episode=1", args)

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_gate_full(self, mock_run):
        mock_run.return_value = {"ok": True}
        cli_gate_full(MagicMock(), "/tmp/script.md", episodes=60)
        skill_id = mock_run.call_args[0][2]
        args = mock_run.call_args[0][3]
        self.assertEqual(skill_id, "gate-full")
        self.assertIn("--full", args)
        self.assertIn("--episodes=60", args)

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_score_deep(self, mock_run):
        mock_run.return_value = {"ok": True}
        cli_score_deep(MagicMock(), "/tmp/script.md", bridge=True)
        skill_id = mock_run.call_args[0][2]
        args = mock_run.call_args[0][3]
        self.assertEqual(skill_id, "score-deep")
        self.assertIn("--mode=deep", args)

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_score_quick(self, mock_run):
        mock_run.return_value = {"ok": True}
        cli_score_quick(MagicMock(), "/tmp/script.md", bridge=True)
        agent_id = mock_run.call_args[0][1]
        skill_id = mock_run.call_args[0][2]
        args = mock_run.call_args[0][3]
        self.assertEqual(agent_id, "review")
        self.assertEqual(skill_id, "score-quick")
        self.assertIn("--mode=quick", args)

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_marketing_kit(self, mock_run):
        mock_run.return_value = {"ok": True, "json": {"titles": []}}
        cli_marketing_kit(
            MagicMock(),
            title="测试剧",
            logline="梗概",
            theme="sweet-pet",
            episodes=80,
        )
        self.assertEqual(mock_run.call_args[0][2], "marketing-kit")

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_compliance_check(self, mock_run):
        mock_run.return_value = {"ok": True}
        cli_compliance_check(MagicMock(), "/tmp/script.md")
        self.assertEqual(mock_run.call_args[0][2], "compliance-check")

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_verify_creation_setting(self, mock_run):
        mock_run.return_value = {"ok": True, "json": {"passed": True}}
        cli_verify_creation_setting(
            MagicMock(),
            "/tmp/world.md",
            "/tmp/ref.md",
            artifact="world",
            entry="from-reference",
        )
        skill_id = mock_run.call_args[0][2]
        args = mock_run.call_args[0][3]
        self.assertEqual(skill_id, "verify-creation")
        self.assertIn("--artifact=world", args)
        self.assertIn("--input=", args[0])

    @patch("apps.creation.orchestration.sub_skill_runner.run_cli_sub_skill")
    def test_cli_verify_creation_brief(self, mock_run):
        mock_run.return_value = {"ok": True, "json": {"ok": True}}
        cli_verify_creation_brief(MagicMock(), "/tmp/ref.md", entry="from-reference")
        skill_id = mock_run.call_args[0][2]
        args = mock_run.call_args[0][3]
        self.assertEqual(skill_id, "verify-creation")
        self.assertIn("--brief-only", args)
        self.assertIn("--entry=from-reference", args)
        self.assertIn("--no-strict", args)

    def test_resolve_registry_script_path_verify_creation(self):
        from apps.workflow.fusion.config_loader import FusionSkillConfig

        try:
            config = FusionSkillConfig()
        except FileNotFoundError:
            self.skipTest("融合技能根目录不可用")
        path = resolve_registry_script_path(
            config,
            {"script": "verify-creation", "type": "cli"},
        )
        self.assertTrue(path.name == "verify-creation.js")
        self.assertTrue(path.is_file())


class SubSkillCliRegistryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from apps.agent.registry import AgentRegistryConfigService

        AgentRegistryConfigService.ensure_defaults()

    def setUp(self):
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def test_run_cli_sub_skill_uses_script_field(self):
        from apps.workflow.fusion.cli_runner import FusionCliRunner

        try:
            runner = FusionCliRunner()
        except (FileNotFoundError, RuntimeError):
            self.skipTest("node 或融合技能根目录不可用")
        runner.run_file = MagicMock(return_value={"ok": True})
        result = run_cli_sub_skill(
            runner,
            "adapt",
            "verify-creation",
            ["--brief-only", "--json"],
        )
        self.assertTrue(result["ok"])
        runner.run_file.assert_called_once()

    def test_run_cli_sub_skill_originality_gate(self):
        from apps.workflow.fusion.cli_runner import FusionCliRunner

        try:
            runner = FusionCliRunner()
        except (FileNotFoundError, RuntimeError):
            self.skipTest("node 或融合技能根目录不可用")
        runner.run_file = MagicMock(return_value={"ok": True, "json": {"passed": True}})
        result = run_cli_sub_skill(
            runner,
            "script",
            "originality-gate",
            ["--artifact=combined", "--json"],
        )
        self.assertTrue(result["ok"])
        runner.run_file.assert_called_once()
