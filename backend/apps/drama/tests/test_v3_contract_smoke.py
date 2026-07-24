# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class V3ContractSmokeTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="v3u", password="pass12345")
        self.client.force_authenticate(user=self.user)

    def test_list_projects_envelope(self) -> None:
        resp = self.client.get("/api/v3/projects/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        self.assertIn("items", body["data"])
        self.assertIsInstance(body["data"]["items"], list)

    def test_create_project_returns_summary(self) -> None:
        resp = self.client.post(
            "/api/v3/projects/",
            {"title": "试写短剧", "entry_type": "original"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["title"], "试写短剧")
        self.assertEqual(data["entry_type"], "original")
        self.assertEqual(data["stage"], "topic")
        self.assertIn("id", data)

    def test_billing_plans_readonly_shell(self) -> None:
        resp = self.client.get("/api/v3/billing/plans/")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()["data"]["items"]
        self.assertEqual(len(items), 3)
        by_id = {p["id"]: p for p in items}
        self.assertEqual(set(by_id), {"basic", "pro", "team"})
        self.assertEqual(by_id["basic"]["name"], "基础版")
        self.assertEqual(by_id["basic"]["price_label"], "¥99/月")
        self.assertEqual(by_id["pro"]["name"], "专业版")
        self.assertEqual(by_id["pro"]["price_label"], "¥299/月")
        self.assertEqual(by_id["team"]["name"], "团队版")
        self.assertEqual(by_id["team"]["price_label"], "¥999/月")
        for plan in items:
            self.assertIn("price_label", plan)
            self.assertIsInstance(plan["features"], list)
            self.assertGreaterEqual(len(plan["features"]), 1)
