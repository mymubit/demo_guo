# -*- coding: utf-8 -*-
"""初始化默认会员套餐"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.membership.models import MembershipPlan

PRO_MATRIX = [
    {"key": "share_link", "label": "作品分享链接", "free": False, "member": True},
    {"key": "priority_queue", "label": "优先创作队列", "free": False, "member": True},
    {"key": "advanced_score", "label": "高级质量审查评分", "free": False, "member": True},
    {"key": "inspiration_plan", "label": "灵感策划", "free": False, "member": True, "member_only": True},
    {"key": "pull_sheet", "label": "拉片分析", "free": False, "member": True, "coming_soon": True, "member_only": True},
]

FLAGSHIP_MATRIX = PRO_MATRIX + [
    {"key": "pdf_export", "label": "PDF / DOCX 导出", "free": False, "member": True},
    {"key": "benchmark", "label": "爆款对标", "free": False, "member": True, "coming_soon": True, "member_only": True},
    {"key": "vip_support", "label": "专属客服支持", "free": False, "member": True},
]

DEFAULT_PLANS = [
    {
        "name": "体验版",
        "price": Decimal("29.00"),
        "validity_days": 30,
        "creation_quota": 0,
        "grant_coins": 200,
        "features": {
            "items": [
                "开通赠送 200 创作币",
                "8 大题材模板",
                "Markdown 格式导出",
                "基础质量审查",
                "7 天作品云端保存",
            ]
        },
        "is_recommended": False,
        "sort_order": 1,
    },
    {
        "name": "专业版",
        "price": Decimal("99.00"),
        "validity_days": 30,
        "creation_quota": 0,
        "grant_coins": 800,
        "features": {
            "items": [
                "开通赠送 800 创作币",
                "所有题材模板 + 定制",
                "4 种格式变体导出",
                "高级质量审查评分",
                "30 天作品云端保存",
                "优先创作队列",
                "作品分享链接",
            ],
            "matrix": PRO_MATRIX,
        },
        "is_recommended": True,
        "sort_order": 2,
    },
    {
        "name": "旗舰版",
        "price": Decimal("999.00"),
        "validity_days": 365,
        "creation_quota": 0,
        "grant_coins": 5000,
        "features": {
            "items": [
                "开通赠送 5000 创作币",
                "所有题材 + 定制模板",
                "完整格式 + PDF + DOCX",
                "S 级质量审查与优化建议",
                "永久作品云端保存",
                "最高优先级队列",
                "高级分享与水印",
                "专属客服支持",
            ],
            "matrix": FLAGSHIP_MATRIX,
        },
        "is_recommended": False,
        "sort_order": 3,
    },
]


class Command(BaseCommand):
    help = "初始化默认会员套餐（体验版 / 专业版 / 旗舰版）"

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for item in DEFAULT_PLANS:
            plan, is_created = MembershipPlan.objects.update_or_create(
                name=item["name"],
                defaults={
                    "price": item["price"],
                    "validity_days": item["validity_days"],
                    "creation_quota": item["creation_quota"],
                    "grant_coins": item.get("grant_coins", 0),
                    "features": item["features"],
                    "is_active": True,
                    "is_recommended": item["is_recommended"],
                    "sort_order": item["sort_order"],
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1
            self.stdout.write(
                f"  - {plan.name}: {plan.price} CNY / {plan.validity_days} days / {plan.grant_coins} 币"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"会员套餐初始化完成（新建 {created}，更新 {updated}）"
            )
        )

        from apps.membership.feature_matrix_service import FeatureMatrixService

        matrix_created = FeatureMatrixService.seed_defaults()
        self.stdout.write(self.style.SUCCESS(f"权益矩阵初始化完成（新建 {matrix_created} 条）"))
