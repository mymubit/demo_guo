# -*- coding: utf-8 -*-
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.membership.models import MembershipPlan

User = get_user_model()


class PortalMembershipApiTests(TestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.user = User.objects.create_user(phone="13900008806", password=self.password)
        self.plan = MembershipPlan.objects.create(
            name="年卡",
            price=Decimal("199"),
            validity_days=365,
            creation_quota=50,
            grant_coins=100,
            is_active=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_plan_list_returns_active_plans(self):
        resp = self.client.get("/api/members/plans/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertGreaterEqual(len(resp.data["data"]), 1)
        self.assertEqual(resp.data["data"][0]["name"], "年卡")

    def test_my_membership_without_subscription_returns_null(self):
        resp = self.client.get("/api/members/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertIsNone(resp.data["data"])

    def test_membership_endpoints_require_auth(self):
        client = APIClient()
        for path in ("/api/members/plans/", "/api/members/me/"):
            resp = client.get(path)
            self.assertEqual(resp.status_code, 200, path)
            self.assertEqual(resp.data["code"], 401, path)
