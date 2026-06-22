# -*- coding: utf-8 -*-
"""Agent 计费测试 — drama.* 新体系。"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.billing.models import CoinLedger, UserWallet
from apps.billing.services import BillingService
from apps.creation.agent_runtime.agent_billing import (
    agent_action_key,
    charge_agent_run,
    ensure_agent_chargeable,
    get_agent_coin_cost,
    refund_agent_run,
    resolve_coin_cost,
)

User = get_user_model()


class DramaAgentBillingTests(TestCase):
    def setUp(self):
        from apps.billing.models import ActionPricing

        self.user = User.objects.create_user(phone="13900009901", password="test-pass-123")
        for key, name, cost, order in [
            ("drama.agent.topic-planner", "选题策划官", 3, 10),
            ("drama.agent.script-writer", "剧本执笔师", 15, 40),
            ("drama.agent.quality-reporter", "质量报告官", 6, 50),
        ]:
            ActionPricing.objects.update_or_create(
                action_key=key,
                defaults={
                    "display_name": name,
                    "coin_cost": cost,
                    "is_active": True,
                    "sort_order": order,
                    "member_only": False,
                },
            )
        self.wallet = BillingService.get_or_create_wallet(self.user)
        UserWallet.objects.filter(pk=self.wallet.pk).update(balance=100)
        self.wallet.refresh_from_db()

    def test_action_key_format(self):
        self.assertEqual(agent_action_key("drama.topic-planner"), "drama.agent.topic-planner")
        self.assertEqual(agent_action_key("drama.script-writer"), "drama.agent.script-writer")
        self.assertEqual(agent_action_key("drama.quality-reporter"), "drama.agent.quality-reporter")

    def test_get_agent_coin_cost_known_roles(self):
        self.assertEqual(get_agent_coin_cost("drama.script-writer"), 15)  # 最高消耗
        self.assertEqual(get_agent_coin_cost("drama.topic-planner"), 3)
        self.assertEqual(get_agent_coin_cost("drama.formatter"), 2)  # 轻量

    def test_get_agent_coin_cost_unknown_uses_default(self):
        cost = get_agent_coin_cost("drama.nonexistent-role")
        self.assertEqual(cost, 5)  # DEFAULT_COIN_COST

    def test_charge_and_refund_idempotent(self):
        run_id = "drama-test-001"
        cost = charge_agent_run(self.user, "drama.topic-planner", run_id=run_id)
        self.assertEqual(cost, 3)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 97)
        # 幂等：重复扣不再减
        charge_agent_run(self.user, "drama.topic-planner", run_id=run_id)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 97)

        refunded = refund_agent_run(self.user, "drama.topic-planner", run_id=run_id)
        self.assertEqual(refunded, 3)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 100)
        # 幂等：重复回补无效
        refund_agent_run(self.user, "drama.topic-planner", run_id=run_id)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 100)

    def test_ensure_chargeable_raises_when_insufficient(self):
        UserWallet.objects.filter(pk=self.wallet.pk).update(balance=1)
        with self.assertRaises(Exception):
            ensure_agent_chargeable(self.user, "drama.script-writer")  # 需要15

    def test_resolve_coin_cost_from_db(self):
        """优先从 ActionPricing 读取价格。"""
        cost = resolve_coin_cost("drama.topic-planner")
        self.assertEqual(cost, 3)  # 与 setUp 中配置一致

    def test_resolve_coin_cost_fallback_to_config(self):
        """无 DB 定价时从配置读取。"""
        cost = resolve_coin_cost("drama.character-designer")
        self.assertEqual(cost, 5)  # DRAMA_AGENT_COIN_COST["drama.character-designer"]
