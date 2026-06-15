# -*- coding: utf-8 -*-
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.billing.commerce_pricing import (
    discount_display_label,
    normalize_discount_percent,
    resolve_charge_price,
)
from apps.billing.models import RechargePackage
from apps.membership.models import MembershipPlan
from apps.orders.services import OrderService

User = get_user_model()


class CommercePricingTests(TestCase):
    def test_resolve_charge_price_with_discount(self):
        charge = resolve_charge_price(
            original=Decimal("100"),
            discount_percent=Decimal("85"),
            manual_price=Decimal("99"),
        )
        self.assertEqual(charge, Decimal("85.00"))

    def test_resolve_charge_price_without_discount(self):
        charge = resolve_charge_price(
            original=Decimal("100"),
            discount_percent=Decimal("100"),
            manual_price=Decimal("88"),
        )
        self.assertEqual(charge, Decimal("88.00"))

    def test_resolve_charge_price_with_string_manual(self):
        charge = resolve_charge_price(
            original=Decimal("99"),
            discount_percent=Decimal("100"),
            manual_price="20.00",
        )
        self.assertEqual(charge, Decimal("20.00"))

    def test_recharge_package_save_with_string_fields(self):
        package = RechargePackage(
            name="基础包",
            price_yuan="20.00",
            original_price_yuan="99",
            discount_percent="100",
            base_coins=2000,
            bonus_coins=500,
        )
        package.save()
        package.refresh_from_db()
        self.assertEqual(package.price_yuan, Decimal("20.00"))
        self.assertEqual(package.bonus_coins, 500)
        self.assertEqual(discount_display_label(Decimal("85")), "8.5折")
        self.assertIsNone(discount_display_label(Decimal("100")))
        self.assertEqual(normalize_discount_percent(None), Decimal("100"))


class DiscountOrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800000001", password="pass")

    def test_membership_order_uses_discounted_price(self):
        plan = MembershipPlan.objects.create(
            name="月卡",
            price=Decimal("99"),
            original_price=Decimal("100"),
            discount_percent=Decimal("80"),
            validity_days=30,
        )
        order, err = OrderService.create_order(self.user, plan.id)
        self.assertIsNone(err)
        self.assertEqual(order.amount, Decimal("80.00"))

    def test_recharge_order_uses_discounted_price(self):
        package = RechargePackage.objects.create(
            name="小包",
            price_yuan=Decimal("9.9"),
            original_price_yuan=Decimal("10"),
            discount_percent=Decimal("90"),
            base_coins=100,
        )
        order, err = OrderService.create_recharge_order(self.user, package.id)
        self.assertIsNone(err)
        self.assertEqual(order.amount, Decimal("9.00"))
