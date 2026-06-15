# -*- coding: utf-8 -*-
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.membership.models import MembershipPlan
from apps.orders.models import Order
from apps.orders.services import OrderService

User = get_user_model()


class PortalOrdersApiTests(TestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.user = User.objects.create_user(phone="13900008804", password=self.password)
        self.other = User.objects.create_user(phone="13900008805", password=self.password)
        self.plan = MembershipPlan.objects.create(
            name="测试月卡",
            price=Decimal("29"),
            validity_days=30,
            creation_quota=5,
            grant_coins=20,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.other_order, _ = OrderService.create_order(self.other, self.plan.id)

    def test_order_list_paginated(self):
        OrderService.create_order(self.user, self.plan.id)
        resp = self.client.get("/api/orders/?page=1&page_size=10")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertIn("pagination", resp.data)
        self.assertGreaterEqual(resp.data["pagination"]["total"], 1)
        self.assertIsInstance(resp.data["data"], list)

    def test_retrieve_other_user_order_returns_404(self):
        resp = self.client.get(f"/api/orders/{self.other_order.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 404)

    def test_create_order_invalid_plan_returns_business_error(self):
        resp = self.client.post(
            "/api/orders/create_order/",
            {
                "plan_id": "00000000-0000-0000-0000-000000000099",
                "payment_method": "mock",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.data["code"], 0)

    @override_settings(ALLOW_MOCK_PAYMENT=True, DEBUG=True)
    def test_create_order_success(self):
        resp = self.client.post(
            "/api/orders/create_order/",
            {"plan_id": str(self.plan.id), "payment_method": "mock"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["code"], 0)
        self.assertIn("order", resp.data["data"])
        self.assertEqual(
            Order.objects.filter(user=self.user, status=Order.STATUS_PENDING).count(),
            1,
        )

    def test_orders_list_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/orders/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 401)
