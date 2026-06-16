# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone

from apps.creation.artifact_service import save_artifact
from apps.creation.models import CreationNode, Project
from apps.creation.workspace.workspace_service import (
    _has_artifact_content,
    _project_can_share,
    build_workspace_payload,
    finalize_workspace_brief,
    generate_skill,
    reconcile_workspace_brief_status,
    recover_stale_workspace_running_state,
)
from apps.creation.tasks import _run_skill_node_core
from apps.billing.services import BillingService

User = get_user_model()


class WorkspaceServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900004401", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="联调测试",
            theme="sweet-pet",
            core_idea="甜宠逆袭",
            episode_count=10,
            pipeline_mode=Project.MODE_WORKSPACE,
            status=Project.STATUS_PENDING,
        )
        save_artifact(
            self.project,
            "project_brief",
            {
                "workingTitle": "联调测试",
                "theme": "sweet-pet",
                "episodeCount": 10,
                "coreHook": "甜宠逆袭",
            },
        )
        CreationNode.objects.create(
            project=self.project,
            node_index=1,
            node_name="立项整理",
            status=CreationNode.STATUS_COMPLETED,
        )

    def test_has_artifact_content_brief(self):
        self.assertTrue(_has_artifact_content(self.project, 1))
        self.assertFalse(_has_artifact_content(self.project, 2))

    def test_build_workspace_payload_fields(self):
        payload = build_workspace_payload(self.project)
        self.assertEqual(payload["project_id"], str(self.project.id))
        self.assertEqual(payload["episode_count"], 10)
        self.assertIn("agents", payload)
        self.assertEqual(len(payload["agents"]), 5)
        self.assertIn("post_script", payload)
        self.assertIn("can_export_zip", payload)
        self.assertIn("can_share", payload)
        self.assertFalse(payload["can_share"])
        brief_agent = payload["agents"][0]
        self.assertTrue(brief_agent["has_content"])
        self.assertEqual(brief_agent.get("content_kind"), "user_confirmed")
        self.assertFalse(brief_agent.get("agent_generated"))
        self.assertIn("readable_markdown", brief_agent)
        self.assertEqual(payload.get("completed_agent_count"), 0)
        self.assertEqual(payload.get("confirmed_skill_count"), 1)
        self.assertIn("execution_plan", payload)
        self.assertIn("stages", payload["execution_plan"])

    def test_build_workspace_payload_skill_orchestration_hints(self):
        payload = build_workspace_payload(self.project)
        first_skill = payload["skills"][0]
        self.assertIn("orchestration_stage_type", first_skill)

    def test_can_share_when_completed(self):
        self.project.status = Project.STATUS_COMPLETED
        self.project.save(update_fields=["status"])
        payload = build_workspace_payload(self.project)
        self.assertTrue(payload["can_share"])
        self.assertTrue(_project_can_share(self.project))

    def test_generate_skill_requires_brief(self):
        empty = Project.objects.create(
            user=self.user,
            title="空项目",
            theme="sweet-pet",
            episode_count=10,
            pipeline_mode=Project.MODE_WORKSPACE,
        )
        with self.assertRaises(PermissionDenied):
            generate_skill(empty, 2)

    def test_generate_skill_node1_not_allowed(self):
        with self.assertRaises(PermissionDenied):
            generate_skill(self.project, 1)

    def test_finalize_workspace_brief_marks_node1_completed(self):
        self.project.nodes.filter(node_index=1).update(
            status=CreationNode.STATUS_PENDING,
            summary_text="",
            completed_at=None,
        )

        finalize_workspace_brief(self.project)

        node = self.project.nodes.get(node_index=1)
        self.assertEqual(node.status, CreationNode.STATUS_COMPLETED)
        self.assertEqual(node.summary_text, "立项参数已确认")
        self.assertIsNotNone(node.completed_at)

    def test_reconcile_workspace_brief_status_repairs_existing_pending(self):
        node = self.project.nodes.get(node_index=1)
        node.status = CreationNode.STATUS_PENDING
        node.summary_text = "立项参数已确认"
        node.completed_at = None
        node.save(update_fields=["status", "summary_text", "completed_at"])

        self.assertTrue(reconcile_workspace_brief_status(self.project))

        node.refresh_from_db()
        self.assertEqual(node.status, CreationNode.STATUS_COMPLETED)
        self.assertIsNotNone(node.completed_at)

    def test_recover_stale_running_node_with_content(self):
        save_artifact(
            self.project,
            "structure_plan",
            {"sixStagePlan": [{"stageIndex": 1}], "totalEpisodes": 10},
        )
        node = CreationNode.objects.create(
            project=self.project,
            node_index=2,
            node_name="结构与世界观",
            status=CreationNode.STATUS_RUNNING,
            started_at=timezone.now() - timedelta(minutes=10),
        )
        self.project.status = Project.STATUS_RUNNING
        self.project.save(update_fields=["status"])

        self.assertTrue(recover_stale_workspace_running_state(self.project))

        node.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(node.status, CreationNode.STATUS_COMPLETED)
        self.assertEqual(self.project.status, Project.STATUS_PENDING)

        payload = build_workspace_payload(self.project)
        self.assertIsNone(payload.get("running_blocker"))
        BillingService.credit(
            self.user,
            100,
            action_key="test.credit",
            reference_id="workspace-service",
            remark="测试余额",
        )
        generate_skill(self.project, 3)

    def test_running_skill_worker_is_idempotent(self):
        CreationNode.objects.create(
            project=self.project,
            node_index=2,
            node_name="结构与世界观",
            status=CreationNode.STATUS_RUNNING,
            started_at=timezone.now(),
        )
        self.project.status = Project.STATUS_RUNNING
        self.project.current_node_index = 2
        self.project.save(update_fields=["status", "current_node_index"])

        result = _run_skill_node_core(str(self.project.id), 2)

        self.assertEqual(result["status"], "skip")
