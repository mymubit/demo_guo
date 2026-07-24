from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("drama", "0007_dramallmcalllog_injection_manifest")]

    operations = [
        migrations.RenameModel(old_name="DramaWorkflowState", new_name="DramaProjectRuntime"),
        migrations.AlterModelTable(name="dramaprojectruntime", table="drama_project_runtime"),
        migrations.RenameField(model_name="dramaprojectruntime", old_name="state", new_name="metadata"),
        migrations.RenameField(model_name="dramaprojectruntime", old_name="version", new_name="revision"),
        migrations.AlterField(
            model_name="dramaprojectruntime",
            name="project",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name="runtime", serialize=False, to="drama.dramaproject"),
        ),
        migrations.RenameField(model_name="dramagenerationjob", old_name="workflow_version", new_name="base_revision"),
    ]
