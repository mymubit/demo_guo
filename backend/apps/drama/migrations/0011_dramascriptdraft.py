from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [('drama', '0010_alter_studiodecision_options_and_more')]

    operations = [
        migrations.CreateModel(
            name='DramaScriptDraft',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('episode_number', models.PositiveIntegerField()),
                ('content', models.TextField(default='')),
                ('updated_by', models.CharField(default='', max_length=128)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='script_drafts', to='drama.dramaproject')),
            ],
            options={'db_table': 'drama_script_draft'},
        ),
        migrations.AddConstraint(model_name='dramascriptdraft', constraint=models.UniqueConstraint(fields=('project', 'episode_number'), name='uniq_project_episode_draft')),
        migrations.AddIndex(model_name='dramascriptdraft', index=models.Index(fields=['project', 'episode_number'], name='drama_scrip_project_67a5e3_idx')),
    ]
