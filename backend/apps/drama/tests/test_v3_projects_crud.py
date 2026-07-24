# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.drama.models import V3Project, V3UsageDailyRollup


class V3ProjectsCrudTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="crud_u", password="pass12345")
        self.other = user_model.objects.create_user(username="crud_other", password="pass12345")
        self.client.force_authenticate(user=self.user)

    def test_create_project_via_post_returns_topic_stage(self) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(
                "/api/v3/projects/",
                {"title": "CRUD 试写", "entry_type": "original"},
                format="json",
            )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["title"], "CRUD 试写")
        self.assertEqual(data["entry_type"], "original")
        self.assertEqual(data["stage"], "topic")
        self.assertIn("id", data)
        self.assertTrue(V3Project.objects.filter(id=data["id"], owner=self.user).exists())

        from apps.drama.models import V3CommandRun

        topic_runs = V3CommandRun.objects.filter(
            owner=self.user,
            project_id=data["id"],
            command_type="generate_topic_brief",
        )
        self.assertTrue(topic_runs.exists())
        self.assertEqual(topic_runs.first().idempotency_key, f"auto-topic:{data['id']}")

    def test_list_excludes_archived_by_default(self) -> None:
        active = V3Project.objects.create(
            owner=self.user, title="活跃", entry_type="original"
        )
        V3Project.objects.create(
            owner=self.user,
            title="已归档",
            entry_type="adapt",
            archived_at=timezone.now(),
        )
        resp = self.client.get("/api/v3/projects/")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()["data"]["items"]
        ids = {item["id"] for item in items}
        self.assertIn(str(active.id), ids)
        self.assertEqual(len(items), 1)

    def test_archive_hides_from_list_unless_include_archived(self) -> None:
        project = V3Project.objects.create(
            owner=self.user, title="待归档", entry_type="original"
        )
        archive_resp = self.client.post(f"/api/v3/projects/{project.id}/archive/")
        self.assertEqual(archive_resp.status_code, 200)
        archived_data = archive_resp.json()["data"]
        self.assertIsNotNone(archived_data["archived_at"])
        project.refresh_from_db()
        self.assertIsNotNone(project.archived_at)

        empty_resp = self.client.get("/api/v3/projects/")
        self.assertEqual(empty_resp.status_code, 200)
        self.assertEqual(empty_resp.json()["data"]["items"], [])

        shown_resp = self.client.get("/api/v3/projects/?include_archived=1")
        self.assertEqual(shown_resp.status_code, 200)
        items = shown_resp.json()["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], str(project.id))
        self.assertIsNotNone(items[0]["archived_at"])

        # 幂等：再次 archive 仍 200
        again = self.client.post(f"/api/v3/projects/{project.id}/archive/")
        self.assertEqual(again.status_code, 200)

    def test_commands_create_project_succeeds_with_project(self) -> None:
        resp = self.client.post(
            "/api/v3/commands/",
            {
                "command_type": "create_project",
                "payload": {"title": "命令创建", "entry_type": "adapt"},
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        run = data["command_run"]
        self.assertEqual(run["command_type"], "create_project")
        self.assertEqual(run["status"], "succeeded")
        self.assertIn("id", run)
        self.assertIn("project_id", run)
        self.assertIn("result_payload", run)
        project = data["project"]
        self.assertEqual(project["title"], "命令创建")
        self.assertEqual(project["entry_type"], "adapt")
        self.assertEqual(project["stage"], "topic")
        self.assertEqual(str(run["project_id"]), project["id"])

    def test_commands_test_model_provider_requires_provider_id(self) -> None:
        """模型试连已 live：缺少 provider_id 时同步失败（非 unsupported）。"""
        resp = self.client.post(
            "/api/v3/commands/",
            {
                "command_type": "test_model_provider",
                "payload": {},
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        run = data["command_run"]
        self.assertEqual(run["status"], "failed")
        self.assertIn("provider_id", run["error_message"])
        self.assertNotEqual(run["status"], "unsupported")

    def test_archive_other_users_project_returns_404(self) -> None:
        foreign = V3Project.objects.create(
            owner=self.other, title="他人项目", entry_type="original"
        )
        resp = self.client.post(f"/api/v3/projects/{foreign.id}/archive/")
        self.assertEqual(resp.status_code, 404)
        foreign.refresh_from_db()
        self.assertIsNone(foreign.archived_at)

    def test_delete_project_removes_row(self) -> None:
        project = V3Project.objects.create(
            owner=self.user, title="待删除", entry_type="original"
        )
        resp = self.client.delete(f"/api/v3/projects/{project.id}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        self.assertTrue(body["data"]["deleted"])
        self.assertEqual(body["data"]["id"], str(project.id))
        self.assertFalse(V3Project.objects.filter(id=project.id).exists())

    def test_delete_project_with_usage_rollup_and_null_sibling(self) -> None:
        """用量日汇总 CASCADE；避免 SET_NULL 撞上 project=null 唯一约束。"""
        project = V3Project.objects.create(
            owner=self.user, title="有用量", entry_type="original"
        )
        day = timezone.localdate()
        V3UsageDailyRollup.objects.create(
            date=day,
            owner=self.user,
            project=None,
            command_type="generate_topic_brief",
            model_name="demo-model",
            provider=None,
            call_count=1,
            success_count=1,
            total_tokens=10,
        )
        V3UsageDailyRollup.objects.create(
            date=day,
            owner=self.user,
            project=project,
            command_type="generate_topic_brief",
            model_name="demo-model",
            provider=None,
            call_count=2,
            success_count=1,
            total_tokens=20,
        )
        resp = self.client.delete(f"/api/v3/projects/{project.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(V3Project.objects.filter(id=project.id).exists())
        self.assertEqual(
            V3UsageDailyRollup.objects.filter(
                owner=self.user, command_type="generate_topic_brief"
            ).count(),
            1,
        )
        remaining = V3UsageDailyRollup.objects.get(
            owner=self.user, command_type="generate_topic_brief"
        )
        self.assertIsNone(remaining.project_id)

    def test_delete_other_users_project_returns_404(self) -> None:
        foreign = V3Project.objects.create(
            owner=self.other, title="他人项目", entry_type="original"
        )
        resp = self.client.delete(f"/api/v3/projects/{foreign.id}/")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(V3Project.objects.filter(id=foreign.id).exists())
