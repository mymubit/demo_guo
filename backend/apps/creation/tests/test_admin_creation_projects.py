# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.creation.models import Project, ProjectFusionArtifact, AgentExecutionRun
from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
from apps.console.creation.project_views import (
    _project_ops_row,
    build_agent_ops_dashboard,
)

User = get_user_model()


class AdminCreationProjectsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(phone="13900003301", password="admin-pass-123")
        self.user = User.objects.create_user(phone="13900003302", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="运营测试项目",
            theme="sweet-pet",
            episode_count=80,
            pipeline_mode=Project.MODE_WORKSPACE,
            creation_entry="from-reference",
        )
        ProjectFusionArtifact.objects.create(
            project=self.project,
            artifact_key="agent_execution_traces",
            payload={"brief": {"execution_trace": [{"id": "brief-gen", "status": "executed"}]}},
        )
        ProjectFusionArtifact.objects.create(
            project=self.project,
            artifact_key="adaptation_meta",
            payload={
                "creationEntry": "from-reference",
                "verifyCreation": {"passed": True, "skipped": False},
                "verifyReports": {
                    "outline": {"passed": True, "skipped": False},
                },
            },
        )

    def test_project_ops_row_includes_verify_and_traces(self):
        row = _project_ops_row(self.project)
        self.assertEqual(row["title"], "运营测试项目")
        self.assertTrue(row["has_agent_traces"])
        self.assertEqual(row["trace_agent_count"], 1)
        self.assertTrue(row["verify_summary"]["hasReports"])
        self.assertEqual(row["user_phone"], "13900003302")
        self.assertEqual(row["execution_run_count"], 0)

    def test_batch_execution_summary_on_list(self):
        run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="world",
            node_index=2,
            status=AgentExecutionRun.STATUS_FAILED,
            error_message="结构生成失败",
        )
        summary = AgentExecutionRunService.batch_project_execution_summary([self.project.id])
        pid = str(self.project.id)
        self.assertEqual(summary[pid]["failed_count"], 1)
        self.assertEqual(summary[pid]["latest_failed_run"]["id"], str(run.id))

        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/admin/creation/projects/", {"keyword": "运营测试"})
        items = res.json().get("data") or []
        self.assertEqual(items[0]["execution_failed_count"], 1)
        self.assertEqual(items[0]["latest_failed_run"]["agent_id"], "world")
        self.assertNotIn("skill_id", items[0]["latest_failed_run"])

    def test_list_filter_has_failed_run(self):
        from apps.drama.models import DramaProject, DramaRoleExecution

        dp = DramaProject.objects.create(
            id=self.project.id,
            project_id=self.project.id,
            user=self.user,
            title=self.project.title,
            genre_code=self.project.theme,
            total_episodes=self.project.episode_count,
        )
        DramaRoleExecution.objects.create(
            drama_project=dp,
            agent_id="drama.topic-planner",
            agent_name_zh="选题策划官",
            status=DramaRoleExecution.Status.FAILED,
            error_message="测试失败",
        )
        other = Project.objects.create(
            user=self.user,
            title="无失败",
            theme="test",
            episode_count=10,
        )
        DramaProject.objects.create(
            id=other.id,
            project_id=other.id,
            user=self.user,
            title="无失败",
            genre_code="test",
            total_episodes=10,
        )
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/admin/creation/projects/", {"has_failed_run": "true"})
        ids = {item["project_id"] for item in res.json().get("data") or []}
        self.assertIn(str(self.project.id), ids)
        self.assertNotIn(str(other.id), ids)

    def test_build_creation_ops_alerts(self):
        from apps.console.creation.project_views import build_creation_ops_alerts

        alerts = build_creation_ops_alerts()
        self.assertGreaterEqual(alerts.get("all", alerts.get("running", 0)), 0)
        self.assertIn("has_failed_run", alerts)
        self.assertIn("running", alerts)

    def test_build_agent_ops_dashboard(self):
        data = build_agent_ops_dashboard(stats_limit=50)
        self.assertIn("registry_version", data)
        self.assertIn("execution", data)
        self.assertGreaterEqual(data.get("drama_projects", 0), 0)
        self.assertGreaterEqual(data.get("from_reference_projects", 0), 1)

    def test_list_requires_admin(self):
        res = self.client.get("/api/admin/creation/projects/")
        self.assertEqual(res.json().get("code"), 401)

        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/admin/creation/projects/")
        self.assertEqual(res.json().get("code"), 403)

    def test_list_returns_paginated_items(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/admin/creation/projects/", {"keyword": "运营测试"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("code"), 0)
        pagination = body.get("pagination") or {}
        self.assertEqual(pagination.get("total"), 1)
        items = body.get("data") or []
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["project_id"], str(self.project.id))
        self.assertTrue(items[0]["has_agent_traces"])

    def test_list_filters_by_status(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/admin/creation/projects/", {"status": "running"})
        self.assertEqual(res.status_code, 200)
        pagination = res.json().get("pagination") or {}
        self.assertEqual(pagination.get("total"), 0)

    def test_list_facets_optional(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/admin/creation/projects/", {"facets": "1"})
        self.assertEqual(res.status_code, 200)
        facets = res.json().get("facets") or {}
        self.assertGreaterEqual(facets.get("all", 0), 1)
        self.assertIn("drama_projects", facets)
        self.assertIn("has_failed_run", facets)

    def test_admin_delete_project(self):
        self.client.force_authenticate(user=self.admin)
        pid = str(self.project.id)
        res = self.client.delete(f"/api/admin/creation/projects/{pid}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("code"), 0)
        self.assertFalse(Project.objects.filter(id=pid).exists())

    def test_admin_delete_running_blocked(self):
        from apps.drama.models import DramaProject, DramaRoleExecution

        dp = DramaProject.objects.create(
            id=self.project.id,
            project_id=self.project.id,
            user=self.user,
            title=self.project.title,
            genre_code=self.project.theme,
            total_episodes=self.project.episode_count,
        )
        DramaRoleExecution.objects.create(
            drama_project=dp,
            agent_id="drama.topic-planner",
            agent_name_zh="选题策划官",
            status=DramaRoleExecution.Status.RUNNING,
        )
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(f"/api/admin/creation/projects/{self.project.id}/")
        self.assertEqual(res.json().get("code"), 403)
