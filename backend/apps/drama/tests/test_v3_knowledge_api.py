# -*- coding: utf-8 -*-
"""P4-W2：Knowledge API（列表 / 搜索 / 详情 / 防穿越）。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.tests.helpers import SKILLS_ROOT

_LIST = "/api/v3/knowledge/"
_DOC = "/api/v3/knowledge/doc/"


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class V3KnowledgeApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="kb_user", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_includes_root_and_sectioned_docs(self) -> None:
        resp = self.client.get(_LIST)
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        items = body["data"]["items"]
        self.assertGreaterEqual(len(items), 1)
        paths = {item["path"] for item in items}
        self.assertIn("README.md", paths)
        self.assertIn("craft/theme-templates.md", paths)
        readme = next(i for i in items if i["path"] == "README.md")
        self.assertEqual(readme["section"], "")
        craft = next(i for i in items if i["path"] == "craft/theme-templates.md")
        self.assertEqual(craft["section"], "craft")
        self.assertTrue(craft["title"])
        self.assertTrue(craft["excerpt"])

    def test_filter_by_section(self) -> None:
        resp = self.client.get(_LIST, {"section": "market"})
        self.assertEqual(resp.status_code, 200, resp.content)
        items = resp.json()["data"]["items"]
        self.assertGreaterEqual(len(items), 1)
        for item in items:
            self.assertEqual(item["section"], "market")
            self.assertTrue(item["path"].startswith("market/"))

    def test_search_q_matches_path_title_or_excerpt(self) -> None:
        resp = self.client.get(_LIST, {"q": "theme-templates"})
        self.assertEqual(resp.status_code, 200, resp.content)
        items = resp.json()["data"]["items"]
        self.assertGreaterEqual(len(items), 1)
        self.assertTrue(any("theme-templates" in i["path"] for i in items))

        resp2 = self.client.get(_LIST, {"q": "题材矩阵"})
        self.assertEqual(resp2.status_code, 200, resp2.content)
        items2 = resp2.json()["data"]["items"]
        self.assertGreaterEqual(len(items2), 1)
        self.assertTrue(
            any(
                "题材矩阵" in i["title"] or "题材矩阵" in i["excerpt"]
                for i in items2
            )
        )

    def test_get_doc_by_path(self) -> None:
        resp = self.client.get(_DOC, {"path": "craft/theme-templates.md"})
        self.assertEqual(resp.status_code, 200, resp.content)
        data = resp.json()["data"]
        self.assertEqual(data["path"], "craft/theme-templates.md")
        self.assertIn("题材矩阵", data["title"])
        self.assertIn("#", data["content"])
        self.assertIn("preset_templates", data["content"])

    def test_reject_path_traversal(self) -> None:
        for bad in (
            "../README.md",
            "craft/../../README.md",
            "/etc/passwd",
            "craft/../../../secret.md",
        ):
            resp = self.client.get(_DOC, {"path": bad})
            self.assertEqual(resp.status_code, 400, bad)
            self.assertNotEqual(resp.json()["code"], 0)

    def test_missing_doc_404(self) -> None:
        resp = self.client.get(_DOC, {"path": "craft/does-not-exist.md"})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["code"], 404)

    def test_unauthenticated_401(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get(_LIST)
        self.assertEqual(resp.status_code, 401)
