# -*- coding: utf-8 -*-
"""创作测试共用辅助。"""
from apps.billing.models import UserWallet
from apps.billing.services import BillingService


def grant_test_coins(user, balance: int = 100) -> None:
    wallet = BillingService.get_or_create_wallet(user)
    UserWallet.objects.filter(pk=wallet.pk).update(balance=balance)
