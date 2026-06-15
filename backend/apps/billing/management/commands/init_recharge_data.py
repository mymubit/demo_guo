# -*- coding: utf-8 -*-
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.billing.models import RechargePackage

DEFAULT_PACKAGES = [
    {
        "name": "基础包",
        "price_yuan": Decimal("20.00"),
        "original_price_yuan": Decimal("30.00"),
        "base_coins": 2000,
        "bonus_coins": 0,
        "sort_order": 10,
    },
    {
        "name": "热门包",
        "price_yuan": Decimal("100.00"),
        "original_price_yuan": Decimal("150.00"),
        "base_coins": 10000,
        "bonus_coins": 500,
        "sort_order": 20,
    },
    {
        "name": "超值包",
        "price_yuan": Decimal("300.00"),
        "original_price_yuan": Decimal("450.00"),
        "base_coins": 30000,
        "bonus_coins": 3000,
        "sort_order": 30,
    },
]


class Command(BaseCommand):
    help = "初始化充值档位"

    def handle(self, *args, **options):
        for item in DEFAULT_PACKAGES:
            RechargePackage.objects.update_or_create(
                name=item["name"],
                defaults={
                    "price_yuan": item["price_yuan"],
                    "original_price_yuan": item.get("original_price_yuan"),
                    "base_coins": item["base_coins"],
                    "bonus_coins": item["bonus_coins"],
                    "is_active": True,
                    "sort_order": item["sort_order"],
                },
            )
        self.stdout.write(self.style.SUCCESS("充值档位已初始化"))
