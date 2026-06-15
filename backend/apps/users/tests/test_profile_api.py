# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class UserProfileApiTests(TestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.user = User.objects.create_user(
            phone="13900008802",
            password=self.password,
            nickname="原昵称",
        )
        self.other = User.objects.create_user(
            phone="13900008803",
            password=self.password,
            nickname="他人",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_profile_get_returns_current_user(self):
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertEqual(resp.data["data"]["phone"], "13900008802")
        self.assertEqual(resp.data["data"]["nickname"], "原昵称")

    def test_profile_update_patch(self):
        resp = self.client.patch(
            "/api/users/me/update/",
            {"nickname": "新昵称", "bio": "简介"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertEqual(resp.data["data"]["nickname"], "新昵称")
        self.assertEqual(resp.data["data"]["bio"], "简介")

    def test_change_password_success(self):
        resp = self.client.post(
            "/api/users/me/change_password/",
            {
                "old_password": self.password,
                "new_password": "NewPass456!",
                "new_password_confirm": "NewPass456!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))

    def test_change_password_wrong_old_password(self):
        resp = self.client.post(
            "/api/users/me/change_password/",
            {
                "old_password": "wrong-old",
                "new_password": "NewPass456!",
                "new_password_confirm": "NewPass456!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 4001)

    def test_profile_unauthenticated_returns_401(self):
        client = APIClient()
        resp = client.get("/api/users/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 401)

    def test_profile_scoped_to_authenticated_user_only(self):
        """资料接口无用户 ID 参数，仅能访问当前登录用户。"""
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.data["data"]["phone"], self.user.phone)
        self.assertNotEqual(resp.data["data"]["phone"], self.other.phone)
