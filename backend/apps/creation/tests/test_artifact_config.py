# -*- coding: utf-8 -*-
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase


class AgentOutputArtifactConfigTests(SimpleTestCase):
    def test_infer_output_artifact_key_reads_agent_registry_outputs(self):
        from apps.creation.monitoring.execution_run_service import AgentExecutionRunService

        result = SimpleNamespace(outputs={"custom_report": {"ok": True}})
        with patch(
            "apps.agent.runtime.get_agent",
            return_value={"id": "custom", "outputs": ["custom_report"]},
        ):
            artifact_key = AgentExecutionRunService.infer_output_artifact_key("custom", result)

        self.assertEqual(artifact_key, "custom_report")

    def test_infer_output_artifact_key_uses_registry_primary_output(self):
        from apps.creation.monitoring.execution_run_service import AgentExecutionRunService

        result = SimpleNamespace(outputs={})
        with patch(
            "apps.agent.runtime.get_agent",
            return_value={"id": "marketing", "outputs": ["marketing_kit"]},
        ):
            artifact_key = AgentExecutionRunService.infer_output_artifact_key("marketing", result)

        self.assertEqual(artifact_key, "marketing_kit")

    def test_infer_output_artifact_key_empty_when_registry_missing(self):
        from apps.creation.monitoring.execution_run_service import AgentExecutionRunService

        result = SimpleNamespace(outputs={})
        with patch("apps.agent.runtime.get_agent", return_value=None):
            with patch("apps.agent.runtime.primary_output_artifact", return_value=""):
                artifact_key = AgentExecutionRunService.infer_output_artifact_key("marketing", result)

        self.assertEqual(artifact_key, "")


class FusionArtifactConfigTests(TestCase):
    def tearDown(self):
        from apps.workflow.pipeline_store import FusionPipelineDbService

        FusionPipelineDbService.clear_caches()

    def test_artifacts_for_node_reads_main_chain_keys(self):
        from apps.workflow.fusion.artifact_registry import FusionArtifactRegistry

        registry = FusionArtifactRegistry()
        self.assertEqual(registry.artifacts_for_node(1), ["project_brief"])
        self.assertEqual(registry.artifacts_for_node(5), ["episode_scripts"])
        self.assertEqual(registry.artifacts_for_node(6), [])

    def test_pipeline_result_sources_include_five_step_defaults(self):
        from apps.workflow.fusion.artifact_registry import FusionArtifactRegistry

        registry = FusionArtifactRegistry()
        by_artifact = {row["artifact_key"]: row for row in registry.pipeline_result_sources()}
        self.assertEqual(by_artifact["project_brief"]["pipeline_result_key"], "project_brief")
        self.assertEqual(by_artifact["structure_plan"]["pipeline_result_key"], "structure")
        self.assertEqual(by_artifact["episode_scripts"]["pipeline_result_key"], "scripts")

    def test_build_pipeline_result_from_project_uses_registry(self):
        from apps.creation.artifact_service import save_artifact
        from apps.creation.models import Project
        from apps.creation.step_mode import build_pipeline_result_from_project
        from apps.users.models import User

        user = User.objects.create_user(phone="13900009901", password="TestPass123!")
        project = Project.objects.create(
            user=user,
            title="mapping test",
            theme="urban",
            core_idea="test",
            episode_count=2,
            format_variant="B",
        )
        save_artifact(project, "project_brief", {"writing_brief": "hello"})
        save_artifact(
            project,
            "episode_scripts",
            {
                "episodes": [
                    {
                        "episodeNumber": 1,
                        "title": "episode 1",
                        "scenes": [],
                    }
                ]
            },
        )

        result = build_pipeline_result_from_project(project)
        self.assertEqual(result["project_brief"].get("writing_brief"), "hello")
        self.assertIn("artifacts", result)
        self.assertIn("episode_scripts", result["artifacts"])
        self.assertIn("episodes", result.get("scripts") or {})
