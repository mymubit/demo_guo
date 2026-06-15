from django.db import migrations, models
from django.db.models import Count


def disambiguate_duplicate_positive_references(apps, schema_editor):
    CoinLedger = apps.get_model("billing", "CoinLedger")
    duplicates = (
        CoinLedger.objects.filter(delta__gt=0)
        .exclude(reference_id="")
        .values("user_id", "action_key", "reference_id")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
    )
    for group in duplicates:
        rows = (
            CoinLedger.objects.filter(
                user_id=group["user_id"],
                action_key=group["action_key"],
                reference_id=group["reference_id"],
                delta__gt=0,
            )
            .order_by("created_at", "id")
            .values_list("id", flat=True)
        )
        for row_id in list(rows)[1:]:
            suffix = str(row_id).replace("-", "")[:8]
            base = group["reference_id"][:55]
            CoinLedger.objects.filter(id=row_id).update(
                reference_id=f"{base}:dup:{suffix}"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0009_delete_pipelinenodeconfig"),
    ]

    operations = [
        migrations.RunPython(disambiguate_duplicate_positive_references, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="coinledger",
            constraint=models.UniqueConstraint(
                fields=("user", "action_key", "reference_id"),
                condition=models.Q(delta__gt=0) & ~models.Q(reference_id=""),
                name="uniq_positive_coin_ledger_reference",
            ),
        ),
    ]
