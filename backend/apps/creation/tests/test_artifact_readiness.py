# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.common.user_messages import humanize_upstream_artifact_message, humanize_user_message
from apps.creation.artifact_readiness import missing_upstream_error, node_has_meaningful_content
from apps.creation.artifact_service import save_artifact
from apps.creation.models import CreationNode, Project
from apps.creation.workspace.workspace_service import (
    _reconcile_workspace_node_status,
    build_workspace_payload,
)

User = get_user_model()


class ArtifactReadinessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900005501", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="就绪测试",
            theme="sweet-pet",
            episode_count=10,
            pipeline_mode=Project.MODE_WORKSPACE,
        )

    def test_humanize_upstream_message(self):
        self.assertEqual(
            humanize_upstream_artifact_message("缺少上游产物: character_bible"),
            "请先生成「角色设计」",
        )
        self.assertEqual(
            humanize_user_message("缺少上游产物: character_bible"),
            "请先生成「角色设计」",
        )

    def test_character_node_requires_real_characters(self):
        save_artifact(self.project, "character_bible", {"characters": []})
        self.assertFalse(node_has_meaningful_content(self.project, 3))
        self.assertEqual(missing_upstream_error("character_bible"), "请先生成「角色设计」")

    def test_project_brief_ready_without_node_artifact_key_mapping(self):
        from apps.creation.artifact_readiness import project_brief_ready

        save_artifact(
            self.project,
            "project_brief",
            {
                "theme": "family-revenge",
                "coreHook": "豪门养女被陷害后归来复仇",
                "seedEnriched": True,
            },
        )
        self.assertTrue(project_brief_ready(self.project))
        self.assertTrue(node_has_meaningful_content(self.project, 1))

    def test_project_brief_ready_from_project_fields(self):
        from apps.creation.artifact_readiness import project_brief_ready

        self.project.core_idea = "一句话梗概足够长"
        self.project.theme = "family-revenge"
        self.project.save(update_fields=["core_idea", "theme"])
        self.assertTrue(project_brief_ready(self.project))

    def test_reconcile_stale_running_when_project_failed(self):
        from apps.creation.workspace.workspace_service import _reconcile_stale_running_nodes

        save_artifact(
            self.project,
            "project_brief",
            {"theme": "sweet-pet", "coreHook": "测试梗概", "seedEnriched": True},
        )
        CreationNode.objects.create(
            project=self.project,
            node_index=2,
            node_name="结构与世界观",
            status=CreationNode.STATUS_RUNNING,
            summary_text="正在生成",
        )
        self.project.status = Project.STATUS_FAILED
        self.project.error_message = "请先生成「立项策划」"
        self.project.save(update_fields=["status", "error_message"])

        self.assertTrue(_reconcile_stale_running_nodes(self.project))

        node = CreationNode.objects.get(project=self.project, node_index=2)
        self.assertEqual(node.status, CreationNode.STATUS_FAILED)
        self.assertEqual(node.summary_text, "生成失败")

    def test_reconcile_phantom_completed_character_node(self):
        save_artifact(self.project, "character_bible", {})
        CreationNode.objects.create(
            project=self.project,
            node_index=3,
            node_name="角色设计",
            status=CreationNode.STATUS_COMPLETED,
        )
        self.project.status = Project.STATUS_FAILED
        self.project.error_message = "缺少上游产物: character_bible"
        self.project.save(update_fields=["status", "error_message"])

        self.assertTrue(_reconcile_workspace_node_status(self.project))

        node = CreationNode.objects.get(project=self.project, node_index=3)
        self.project.refresh_from_db()
        self.assertEqual(node.status, CreationNode.STATUS_PENDING)
        self.assertEqual(self.project.status, Project.STATUS_PENDING)
        self.assertEqual(self.project.error_message, "")

        payload = build_workspace_payload(self.project)
        char_agent = payload["agents"][2]
        self.assertFalse(char_agent["has_content"])
        self.assertEqual(char_agent["content_kind"], "empty")
