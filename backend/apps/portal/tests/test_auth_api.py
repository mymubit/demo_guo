# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class PortalAuthApiTests(TestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.user = User.objects.create_user(
            phone="13900008801",
            password=self.password,
            nickname="测试用户",
        )
        self.client = APIClient()

    def test_login_success_returns_tokens_and_user(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"phone": "13900008801", "password": self.password},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        data = resp.data["data"]
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user"]["phone"], "13900008801")

    def test_login_wrong_password_returns_error(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"phone": "13900008801", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 4001)

    def test_refresh_returns_access_token(self):
        refresh = RefreshToken.for_user(self.user)
        resp = self.client.post(
            "/api/auth/refresh/",
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertNotIn("data", resp.data)

    def test_protected_endpoint_requires_auth(self):
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 401)
