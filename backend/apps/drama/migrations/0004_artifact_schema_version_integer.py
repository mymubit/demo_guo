# Generated manually for centralized contract schema_version migration

import re

from django.db import migrations, models


def _parse_schema_version(value: object) -> int:
    if isinstance(value, int):
        return value if value >= 1 else 1
    if isinstance(value, str):
        match = re.search(r"(\d+)", value)
        if match:
            return max(1, int(match.group(1)))
    return 1


def forwards_convert_schema_versions(apps, schema_editor):
    DramaArtifactVersion = apps.get_model("drama", "DramaArtifactVersion")
    for record in DramaArtifactVersion.objects.all().iterator():
        converted = _parse_schema_version(record.schema_version)
        if record.schema_version != converted:
            record.schema_version = converted
            record.save(update_fields=["schema_version"])


class Migration(migrations.Migration):

    dependencies = [
        ("drama", "0003_generation_job_owner"),
    ]

    operations = [
        migrations.RunPython(
            forwards_convert_schema_versions,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="dramaartifactversion",
            name="schema_version",
            field=models.PositiveIntegerField(verbose_name="Schema 版本"),
        ),
    ]
