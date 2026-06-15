# -*- coding: utf-8 -*-
from django.db import migrations


NEW_ITEMS = [
    {
        "feature_key": "membership_open_grant",
        "label": "开通赠送创作币",
        "free": False,
        "member": True,
        "sort_order": 45,
    },
    {
        "feature_key": "recharge_bonus_coins",
        "label": "充值额外赠送创作币",
        "free": False,
        "member": True,
        "sort_order": 50,
    },
]


def seed_matrix_items(apps, schema_editor):
    Model = apps.get_model("membership", "MembershipFeatureMatrixItem")
    for item in NEW_ITEMS:
        Model.objects.update_or_create(
            feature_key=item["feature_key"],
            defaults={
                "label": item["label"],
                "free": item["free"],
                "member": item["member"],
                "coming_soon": False,
                "member_only": False,
                "is_active": True,
                "sort_order": item["sort_order"],
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0004_membershipplan_discount"),
    ]

    operations = [
        migrations.RunPython(seed_matrix_items, migrations.RunPython.noop),
    ]
