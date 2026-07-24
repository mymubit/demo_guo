# -*- coding: utf-8 -*-
"""旧 /api/v2 统一 410 Gone。"""
from rest_framework.test import APITestCase


class V2GoneTests(APITestCase):
    def test_studio_bootstrap_returns_410(self) -> None:
        resp = self.client.get("/api/v2/studio/bootstrap/")
        self.assertEqual(resp.status_code, 410)
        body = resp.json()
        self.assertEqual(body["code"], 410)
        self.assertIn("/api/v3", body["message"])

    def test_v2_root_returns_410(self) -> None:
        resp = self.client.get("/api/v2/")
        self.assertEqual(resp.status_code, 410)
        self.assertIn("/api/v3", resp.json()["message"])

    def test_v2_post_returns_410(self) -> None:
        resp = self.client.post("/api/v2/studio/anything/", {}, format="json")
        self.assertEqual(resp.status_code, 410)
        self.assertIn("/api/v3", resp.json()["message"])
