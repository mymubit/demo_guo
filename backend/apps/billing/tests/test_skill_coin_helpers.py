# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.billing.models import CoinLedger
from apps.billing.services import (
    BillingService,
    check_and_charge_coins,
    refund_coins,
)

User = get_user_model()


class SkillCoinHelperTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800008801", password="pass")
        BillingService.credit(
            self.user,
            50,
            action_key="test.grant",
            reference_id="skill-helper-setup",
            remark="测试入账",
        )

    def test_check_and_charge_coins_success(self):
        before = BillingService.get_balance(self.user)
        ok, message = check_and_charge_coins(
            user_id=self.user.id,
            amount=10,
            description="技能调用：creation.structure",
            reference_id="skill_pre_trace_1",
        )
        self.assertTrue(ok)
        self.assertEqual(message, "")
        self.assertEqual(BillingService.get_balance(self.user), before - 10)

    def test_check_and_charge_coins_insufficient(self):
        before = BillingService.get_balance(self.user)
        ok, message = check_and_charge_coins(
            user_id=self.user.id,
            amount=before + 1,
            description="技能调用：creation.structure",
            reference_id="skill_pre_trace_2",
        )
        self.assertFalse(ok)
        self.assertIn("不足", message)
        self.assertEqual(BillingService.get_balance(self.user), before)

    def test_refund_coins_idempotent(self):
        before = BillingService.get_balance(self.user)
        check_and_charge_coins(
            user_id=self.user.id,
            amount=10,
            description="技能调用：creation.adapt",
            reference_id="skill_pre_trace_3",
        )
        refund_coins(
            user_id=self.user.id,
            amount=10,
            description="技能失败回补",
            reference_id="skill_pre_trace_3",
        )
        refund_coins(
            user_id=self.user.id,
            amount=10,
            description="技能失败回补",
            reference_id="skill_pre_trace_3",
        )
        self.assertEqual(BillingService.get_balance(self.user), before)
        self.assertEqual(
            CoinLedger.objects.filter(
                user=self.user,
                reference_id="skill_pre_trace_3",
                delta__gt=0,
            ).count(),
            1,
        )
