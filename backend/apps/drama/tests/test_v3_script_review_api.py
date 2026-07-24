# -*- coding: utf-8 -*-
"""独立剧本评审 CRUD API。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from apps.drama.models import ScriptReview, V3Project

_LIST = "/api/v3/reviews/"


class V3ScriptReviewApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="review_api", password="pass12345"
        )
        self.other = user_model.objects.create_user(
            username="review_other", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.project = V3Project.objects.create(
            owner=self.user,
            title="我的项目",
            entry_type=V3Project.EntryType.ORIGINAL,
        )

    def test_create_paste_review(self) -> None:
        resp = self.client.post(
            _LIST,
            {"title": "粘贴稿", "script_text": "第一行\n第二行"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["source_type"], "paste")
        self.assertEqual(body["data"]["script_text"], "第一行\n第二行")

    def test_create_upload_txt(self) -> None:
        upload = SimpleUploadedFile(
            "demo.txt", "上传正文内容".encode("utf-8"), content_type="text/plain"
        )
        resp = self.client.post(
            _LIST,
            {"file": upload, "title": "上传稿"},
            format="multipart",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        data = resp.json()["data"]
        self.assertEqual(data["source_type"], "upload")
        self.assertEqual(data["source_filename"], "demo.txt")
        self.assertIn("上传正文", data["script_text"])

    def test_reject_docx_upload(self) -> None:
        upload = SimpleUploadedFile(
            "demo.docx", b"PK\x03\x04fake", content_type="application/octet-stream"
        )
        resp = self.client.post(_LIST, {"file": upload}, format="multipart")
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_list_only_own(self) -> None:
        ScriptReview.objects.create(
            owner=self.user,
            title="我的",
            source_type=ScriptReview.SourceType.PASTE,
            script_text="a",
        )
        ScriptReview.objects.create(
            owner=self.other,
            title="他人",
            source_type=ScriptReview.SourceType.PASTE,
            script_text="b",
        )
        resp = self.client.get(_LIST)
        self.assertEqual(resp.status_code, 200, resp.content)
        items = resp.json()["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "我的")
        self.assertNotIn("script_text", items[0])

    def test_detail_and_foreign_404(self) -> None:
        review = ScriptReview.objects.create(
            owner=self.user,
            project=self.project,
            title="详情",
            source_type=ScriptReview.SourceType.PASTE,
            script_text="正文",
        )
        resp = self.client.get(f"{_LIST}{review.id}/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["data"]["project_id"], str(self.project.id))

        self.client.force_authenticate(user=self.other)
        resp2 = self.client.get(f"{_LIST}{review.id}/")
        self.assertEqual(resp2.status_code, 404, resp2.content)

    def test_link_foreign_project_rejected(self) -> None:
        foreign = V3Project.objects.create(
            owner=self.other,
            title="别人的",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        resp = self.client.post(
            _LIST,
            {
                "script_text": "正文",
                "project_id": str(foreign.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 404, resp.content)
