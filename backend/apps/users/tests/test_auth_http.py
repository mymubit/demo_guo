# -*- coding: utf-8 -*-
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

User = get_user_model()


@override_settings(ROOT_URLCONF="config.urls")
class AuthHttpSemanticsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="auth_probe", password="pass-12345")

    def test_login_success_returns_http_200_with_tokens(self):
        resp = self.client.post(
            "/api/v1/auth/token/",
            {"username": "auth_probe", "password": "pass-12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertIn("access", resp.data["data"])

    def test_login_wrong_password_returns_http_401(self):
        resp = self.client.post(
            "/api/v1/auth/token/",
            {"username": "auth_probe", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.data["code"], 401)
        self.assertIn("密码", resp.data["message"])

    def test_me_without_token_returns_http_401(self):
        resp = self.client.get("/api/v1/auth/me/")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.data["code"], 401)
