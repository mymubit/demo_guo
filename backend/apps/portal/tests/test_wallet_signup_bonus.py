# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.billing.models import CoinLedger, SiteCoinSettings

User = get_user_model()


class WalletSignupBonusTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        settings_obj = SiteCoinSettings.load()
        settings_obj.signup_bonus = 50
        settings_obj.save(update_fields=["signup_bonus"])
        self.user = User.objects.create_user(phone="13900008920", password="test-pass-123")
        self.client.force_authenticate(user=self.user)

    def test_first_wallet_get_creates_wallet_and_grants_bonus(self):
        resp = self.client.get("/api/billing/wallet/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertEqual(resp.data["data"]["balance"], 50)
        self.assertTrue(
            CoinLedger.objects.filter(user=self.user, action_key="signup.bonus").exists()
        )

    @override_settings(ALLOW_MOCK_PAYMENT=True, DEBUG=True)
    def test_regular_user_mock_pay_allowed_in_debug(self):
        from apps.membership.models import MembershipPlan
        from apps.orders.models import Order

        plan = MembershipPlan.objects.create(
            name="测试月卡",
            price=9.9,
            grant_coins=10,
            validity_days=30,
            is_active=True,
        )
        create_resp = self.client.post(
            "/api/orders/create_order/",
            {"plan_id": plan.id, "payment_method": "mock"},
            format="json",
        )
        self.assertIn(create_resp.status_code, (200, 201))
        order_no = create_resp.data["data"]["order"]["order_no"]
        pay_resp = self.client.post(
            "/api/orders/mock_pay/",
            {"order_no": order_no},
            format="json",
        )
        self.assertEqual(pay_resp.status_code, 200)
        self.assertEqual(pay_resp.data["code"], 0)
        order = Order.objects.get(order_no=order_no)
        self.assertEqual(order.status, Order.STATUS_PAID)

    @override_settings(ALLOW_MOCK_PAYMENT=False, DEBUG=True)
    def test_mock_pay_rejected_when_disabled(self):
        from apps.membership.models import MembershipPlan

        plan = MembershipPlan.objects.create(
            name="测试月卡2",
            price=9.9,
            grant_coins=10,
            validity_days=30,
            is_active=True,
        )
        create_resp = self.client.post(
            "/api/orders/create_order/",
            {"plan_id": plan.id, "payment_method": "mock"},
            format="json",
        )
        order_no = create_resp.data["data"]["order"]["order_no"]
        pay_resp = self.client.post(
            "/api/orders/mock_pay/",
            {"order_no": order_no},
            format="json",
        )
        self.assertEqual(pay_resp.status_code, 200)
        self.assertNotEqual(pay_resp.data["code"], 0)
