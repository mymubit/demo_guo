# -*- coding: utf-8 -*-
"""API 权限与契约集成测试。"""
from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.tests.helpers import FIXTURE_SETTINGS, SKILLS_ROOT, auth_client, create_project, create_user


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=False,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class DramaApiTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.other = create_user(username="other")
        self.staff = User.objects.create_user(
            username="admin",
            password="test-pass-123",
            is_staff=True,
        )
        self.project = create_project(self.user)
        self.client = auth_client(self.user)

    def test_list_projects_requires_auth(self):
        resp = self.client.get("/api/v1/drama/projects/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)

    def test_settings_put_requires_if_match(self):
        resp = self.client.put(
            f"/api/v1/drama/projects/{self.project.id}/settings/",
            FIXTURE_SETTINGS,
            format="json",
        )
        self.assertEqual(resp.data["code"], 4001)

    def test_settings_put_with_etag(self):
        payload = dict(FIXTURE_SETTINGS)
        payload["project_id"] = str(self.project.id)
        resp = self.client.put(
            f"/api/v1/drama/projects/{self.project.id}/settings/",
            payload,
            format="json",
            HTTP_IF_MATCH="1",
        )
        self.assertEqual(resp.data["code"], 0)
        self.assertEqual(resp["ETag"], "2")

    def test_other_user_cannot_read_project(self):
        client = auth_client(self.other)
        resp = client.get(f"/api/v1/drama/projects/{self.project.id}/workflow/")
        self.assertEqual(resp.data["code"], 403)

    def test_admin_config_forbidden_for_regular_user(self):
        resp = self.client.get("/api/v1/drama/admin/config/")
        self.assertEqual(resp.data["code"], 403)

    def test_admin_config_readable_by_staff(self):
        client = auth_client(self.staff)
        resp = client.get("/api/v1/drama/admin/config/")
        self.assertEqual(resp.data["code"], 0)

    def test_generation_disabled_without_llm(self):
        resp = self.client.post(
            f"/api/v1/drama/projects/{self.project.id}/generation/start/",
            {
                "command_id": "api-gen-disabled",
                "expected_version": 0,
                "role": "drama.topic-director",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 202)
        job_id = resp.data["data"]["job_id"]
        status_resp = self.client.get(
            f"/api/v1/drama/projects/{self.project.id}/generation/{job_id}/"
        )
        self.assertEqual(status_resp.data["data"]["status"], "disabled")

    def test_workflow_command_api(self):
        resp = self.client.post(
            f"/api/v1/drama/projects/{self.project.id}/workflow/commands/",
            {
                "command_id": "api-cmd-1",
                "event": "project_brief_completed",
                "expected_version": 0,
            },
            format="json",
        )
        self.assertEqual(resp.data["code"], 0)
        self.assertEqual(resp.data["data"]["current_phase"], "blueprint")

    def test_theme_matrix_endpoint(self):
        resp = self.client.get("/api/v1/drama/theme-matrix/")
        self.assertEqual(resp.data["code"], 0)
        self.assertIn("dim_order", resp.data["data"])
        self.assertIn("axes", resp.data["data"])

    def test_generation_start_returns_unified_job(self):
        resp = self.client.post(
            f"/api/v1/drama/projects/{self.project.id}/generation/start/",
            {
                "command_id": "api-gen-1",
                "expected_version": 0,
                "role": "drama.topic-director",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 202)
        data = resp.data["data"]
        self.assertIn("job_id", data)
        self.assertIn("status", data)
        self.assertIn("project_id", data)
        self.assertIn("project_id", data)
        self.assertIn("role", data)
        self.assertIn("command_id", data)
        self.assertEqual(data["project_id"], str(self.project.id))

    def test_external_review_job_access_without_project(self):
        resp = self.client.post(
            "/api/v1/drama/external-script-reviews/",
            {
                "command_id": "ext-1",
                "scoring_preset": "standard",
                "check_mode": "standard",
                "script_content": "测试剧本",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 202)
        job_id = resp.data["data"]["job_id"]
        status_resp = self.client.get(f"/api/v1/drama/jobs/{job_id}/")
        self.assertEqual(status_resp.data["code"], 0)
        self.assertEqual(status_resp.data["data"]["job_id"], job_id)

    def test_external_review_multipart_without_project_id(self):
        """上传文件且不带 project_id 时不应因 null UUID 校验失败。"""
        from django.core.files.uploadedfile import SimpleUploadedFile

        uploaded = SimpleUploadedFile(
            "sample.txt",
            "第一章\n外部剧本文本内容".encode("utf-8"),
            content_type="text/plain",
        )
        resp = self.client.post(
            "/api/v1/drama/external-script-reviews/",
            {
                "command_id": "ext-multipart-1",
                "scoring_preset": "standard",
                "check_mode": "standard",
                "file": uploaded,
            },
            format="multipart",
        )
        self.assertEqual(resp.status_code, 202, resp.data)
        self.assertIsNone(resp.data["data"].get("project_id"))
        self.assertTrue(resp.data["data"]["job_id"])

    def test_other_user_cannot_read_orphan_job(self):
        resp = self.client.post(
            "/api/v1/drama/external-script-reviews/",
            {
                "command_id": "ext-2",
                "scoring_preset": "standard",
                "check_mode": "standard",
                "script_content": "私密剧本",
            },
            format="json",
        )
        job_id = resp.data["data"]["job_id"]
        other = auth_client(self.other)
        denied = other.get(f"/api/v1/drama/jobs/{job_id}/")
        self.assertEqual(denied.data["code"], 403)

    def test_list_external_script_reviews_for_owner(self):
        created = self.client.post(
            "/api/v1/drama/external-script-reviews/",
            {
                "command_id": "ext-list-1",
                "scoring_preset": "standard",
                "check_mode": "standard",
                "script_content": "列表可见剧本",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 202)
        job_id = created.data["data"]["job_id"]

        listed = self.client.get("/api/v1/drama/external-script-reviews/")
        self.assertEqual(listed.data["code"], 0)
        items = listed.data["data"]["items"]
        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0]["job_id"], job_id)

        other = auth_client(self.other)
        other_listed = other.get("/api/v1/drama/external-script-reviews/")
        self.assertEqual(other_listed.data["code"], 0)
        other_ids = {item["job_id"] for item in other_listed.data["data"]["items"]}
        self.assertNotIn(job_id, other_ids)

    def test_reprocess_external_review_from_llm_logs(self):
        import json

        from apps.drama.models import DramaGenerationJob, DramaLlmCallLog
        from apps.drama.tests.helpers import FIXTURES

        job = DramaGenerationJob.objects.create(
            owner=self.user,
            project=None,
            job_type=DramaGenerationJob.JobType.EXTERNAL_REVIEW,
            status=DramaGenerationJob.Status.FAILED,
            command_id="ext-reprocess-1",
            error_message="合规子任务失败",
            request_payload={
                "command_id": "ext-reprocess-1",
                "script_content": "测试剧本",
                "scoring_preset": "standard",
                "check_mode": "standard",
                "actor": self.user.username,
                "scoring_mode": "external",
                "source_filename": "测试.txt",
                "script_title": "测试剧本",
            },
        )
        quality = dict(FIXTURES["quality_report"])
        quality["resolved_script_key"] = "external_script"
        # 模拟当时松散结构：dimensions 为数组
        quality_loose = {
            "drama_title": quality["drama_title"],
            "overall_score": quality["overall_score"],
            "grade": quality["grade"],
            "needs_revision": quality["needs_revision"],
            "dimensions": [
                {"name": "格式规范", "score": 82, "evidence": [], "deduction_reasons": []},
                {"name": "叙事效率", "score": 82, "evidence": [], "deduction_reasons": []},
            ],
        }
        compliance = dict(FIXTURES["compliance_report"])
        compliance["resolved_script_key"] = "external_script"

        for purpose, payload in (
            (DramaLlmCallLog.Purpose.QUALITY_SCORING, quality_loose),
            (DramaLlmCallLog.Purpose.COMPLIANCE_CHECK, compliance),
        ):
            content = json.dumps(payload, ensure_ascii=False)
            DramaLlmCallLog.objects.create(
                generation_job=job,
                actor=self.user.username,
                role="drama.script-scorer",
                purpose=purpose,
                model_name="test-model",
                status=DramaLlmCallLog.Status.SUCCESS,
                response_text=content,
                response_body={
                    "choices": [{"message": {"role": "assistant", "content": content}}]
                },
            )

        resp = self.client.post(f"/api/v1/drama/jobs/{job.id}/reprocess/")
        self.assertEqual(resp.data["code"], 0, resp.data)
        self.assertEqual(resp.data["data"]["status"], "completed")
        self.assertIn("quality_report", resp.data["data"]["result"])
        self.assertIn("compliance_report", resp.data["data"]["result"])
        job.refresh_from_db()
        self.assertEqual(job.status, DramaGenerationJob.Status.COMPLETED)
        self.assertEqual(job.error_message, "")

    def test_delete_external_review_job(self):
        from apps.drama.models import DramaGenerationJob

        job = DramaGenerationJob.objects.create(
            owner=self.user,
            project=None,
            job_type=DramaGenerationJob.JobType.EXTERNAL_REVIEW,
            status=DramaGenerationJob.Status.FAILED,
            command_id="ext-delete-1",
            request_payload={
                "command_id": "ext-delete-1",
                "actor": self.user.username,
                "script_title": "待删剧本",
            },
        )
        resp = self.client.delete(f"/api/v1/drama/jobs/{job.id}/")
        self.assertEqual(resp.data["code"], 0, resp.data)
        self.assertTrue(resp.data["data"]["deleted"])
        self.assertFalse(DramaGenerationJob.objects.filter(id=job.id).exists())

        other_job = DramaGenerationJob.objects.create(
            owner=self.other,
            project=None,
            job_type=DramaGenerationJob.JobType.EXTERNAL_REVIEW,
            status=DramaGenerationJob.Status.COMPLETED,
            command_id="ext-delete-2",
            request_payload={"command_id": "ext-delete-2", "actor": self.other.username},
        )
        denied = self.client.delete(f"/api/v1/drama/jobs/{other_job.id}/")
        self.assertEqual(denied.data["code"], 403)

    def test_project_summary_includes_entry_type(self):
        resp = self.client.get("/api/v1/drama/projects/")
        self.assertEqual(resp.data["code"], 0)
        item = resp.data["data"][0]
        self.assertEqual(item["entry_type"], "original_track")
