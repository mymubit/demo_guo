# -*- coding: utf-8 -*-
"""Legacy 表已删除后的编辑器保存测试。"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import Project
from apps.creation.workspace.workspace_editor import apply_editor_save

User = get_user_model()


class LegacyTableRemovedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900008801", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="停写测试",
            theme="sweet-pet",
            core_idea="测试",
            episode_count=10,
            pipeline_mode=Project.MODE_WORKSPACE,
        )
        save_artifact(
            self.project,
            "project_brief",
            {"workingTitle": "停写测试", "theme": "sweet-pet", "episodeCount": 10},
        )

    def test_editor_save_persists_artifact_only(self):
        apply_editor_save(
            self.project,
            1,
            {"fields": [{"key": "themeDisplayName", "value": "甜宠测试"}]},
        )
        payload = get_artifact(self.project, "project_brief") or {}
        self.assertEqual(payload.get("themeDisplayName"), "甜宠测试")

    def test_workspace_catalog_includes_adapt_agent(self):
        AgentDefinitionService.ensure_defaults()
        from apps.creation.agent_runtime.workspace import build_workspace_catalog

        catalog = build_workspace_catalog()
        agent_ids = [a.get("agent_id") for a in (catalog.get("agents") or [])]
        self.assertIn("adapt", agent_ids)

    def test_record_sub_skill_is_noop(self):
        from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
        from apps.creation.models import AgentExecutionRun

        with AgentExecutionRunService.run_scope(
            self.project,
            agent_id="brief",
            node_index=1,
        ) as run:
            AgentExecutionRunService.record_sub_skill("test-skill", "executed")
            AgentExecutionRunService.finish_run(run, AgentExecutionRun.STATUS_COMPLETED)
        self.assertEqual(run.status, AgentExecutionRun.STATUS_COMPLETED)
