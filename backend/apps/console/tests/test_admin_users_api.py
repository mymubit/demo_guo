# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class AdminUsersApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            phone="13900008904",
            password="admin-pass-123",
        )
        self.user = User.objects.create_user(
            phone="13900008905",
            password="test-pass-123",
            nickname="普通用户",
        )
        self.client = APIClient()

    def test_list_requires_auth(self):
        resp = self.client.get("/api/admin/users/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get("code"), 401)

    def test_list_requires_admin(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/admin/users/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get("code"), 403)

    def test_admin_list_paginated(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/admin/users/?page=1&page_size=10")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body.get("code"), 0)
        self.assertIn("pagination", body)
        self.assertGreaterEqual(body["pagination"]["total"], 2)
        self.assertIsInstance(body.get("data"), list)

    def test_admin_list_keyword_search(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/admin/users/?keyword=普通")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body.get("code"), 0)
        self.assertGreaterEqual(len(body.get("data") or []), 1)
