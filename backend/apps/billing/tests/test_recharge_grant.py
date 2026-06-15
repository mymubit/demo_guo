# -*- coding: utf-8 -*-
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.billing.models import RechargePackage
from apps.billing.recharge_grant import resolve_recharge_grant_coins
from apps.membership.models import MembershipPlan
from apps.membership.services import MembershipService
from apps.orders.services import OrderService

User = get_user_model()


class RechargeGrantCoinsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800000002", password="pass")
        self.package = RechargePackage.objects.create(
            name="基础包",
            price_yuan=Decimal("20"),
            base_coins=100,
            bonus_coins=30,
        )

    def test_non_member_gets_base_only(self):
        grant = resolve_recharge_grant_coins(self.package, self.user)
        self.assertEqual(grant["base_coins"], 100)
        self.assertEqual(grant["bonus_coins"], 0)
        self.assertEqual(grant["total_coins"], 100)
        self.assertFalse(grant["member_bonus_eligible"])

    def test_member_gets_bonus(self):
        plan = MembershipPlan.objects.create(
            name="月卡",
            price=Decimal("29"),
            validity_days=30,
        )
        MembershipService.activate_membership(self.user, plan)
        grant = resolve_recharge_grant_coins(self.package, self.user)
        self.assertEqual(grant["bonus_coins"], 30)
        self.assertEqual(grant["total_coins"], 130)

    def test_recharge_order_respects_membership(self):
        order, err = OrderService.create_recharge_order(self.user, self.package.id)
        self.assertIsNone(err)
        self.assertEqual(order.coins_granted, 100)
