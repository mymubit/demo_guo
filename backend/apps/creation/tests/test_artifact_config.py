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

    def test_artifacts_for_node_reads_db_extra_artifact_keys(self):
        from apps.workflow.fusion.artifact_registry import FusionArtifactRegistry
        from apps.workflow.pipeline_store import FusionPipelineDbService
        from apps.workflow.models import FusionPipelineNode, FusionPipelinePack

        pack = FusionPipelinePack.objects.create(version="test-extra-artifacts", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-6-review",
            chain_order=1,
            website_index=6,
            name="质检审查",
            output_key="qualityReport",
            artifact_key="quality_report",
            extra_artifact_keys=["gate_full", "compliance"],
            fusion_status="reviewing",
        )
        FusionPipelineDbService.clear_caches()

        registry = FusionArtifactRegistry()

        self.assertEqual(
            registry.artifacts_for_node(6),
            ["quality_report", "gate_full", "compliance"],
        )

    def test_pipeline_result_key_reads_db_config(self):
        from apps.workflow.fusion.artifact_registry import FusionArtifactRegistry
        from apps.workflow.pipeline_store import FusionPipelineDbService
        from apps.workflow.models import FusionPipelineNode, FusionPipelinePack

        pack = FusionPipelinePack.objects.create(version="test-pipeline-result-key", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-2-structure",
            chain_order=1,
            website_index=2,
            name="结构规划",
            artifact_key="structure_plan",
            pipeline_result_key="structure",
        )
        FusionPipelineDbService.clear_caches()

        registry = FusionArtifactRegistry()
        self.assertEqual(registry.pipeline_result_key_for_artifact("structure_plan"), "structure")
        sources = registry.pipeline_result_sources()
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["pipeline_result_key"], "structure")

    def test_build_pipeline_result_from_project_uses_registry(self):
        from apps.creation.artifact_service import save_artifact
        from apps.creation.models import Project
        from apps.creation.step_mode import build_pipeline_result_from_project
        from apps.workflow.pipeline_store import FusionPipelineDbService
        from apps.workflow.models import FusionPipelineNode, FusionPipelinePack
        from apps.users.models import User

        user = User.objects.create_user(phone="13900009901", password="TestPass123!")
        project = Project.objects.create(
            user=user,
            title="映射测试",
            theme="urban",
            core_idea="测试",
            episode_count=2,
            format_variant="B",
        )
        pack = FusionPipelinePack.objects.create(version="test-build-pipeline-result", is_active=True)
        for order, spec in enumerate(
            [
                ("node-1-input", 1, "project_brief", "project_brief"),
                ("node-5-script", 2, "episode_scripts", "scripts"),
            ],
            start=1,
        ):
            FusionPipelineNode.objects.create(
                pack=pack,
                fusion_node_id=spec[0],
                chain_order=order,
                website_index=spec[1],
                name=spec[0],
                artifact_key=spec[2],
                pipeline_result_key=spec[3],
            )
        FusionPipelineDbService.clear_caches()
        save_artifact(project, "project_brief", {"writing_brief": "hello"})
        save_artifact(
            project,
            "episode_scripts",
            {
                "episodes": [
                    {
                        "episodeNumber": 1,
                        "title": "第一集",
                        "scenes": [],
                    }
                ]
            },
        )

        FusionPipelineDbService.clear_caches()

        result = build_pipeline_result_from_project(project)
        self.assertEqual(result["project_brief"].get("writing_brief"), "hello")
        self.assertIn("artifacts", result)
        self.assertIn("episode_scripts", result["artifacts"])
        self.assertIn("episodes", result.get("scripts") or {})
