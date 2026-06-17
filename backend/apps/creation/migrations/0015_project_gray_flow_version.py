# Generated migration: Project 灰度工作流版本追踪字段扩展

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creation', '0014_creation_task_and_project_status_sync'),
    ]

    operations = [
        # 新增：记录创作命中了哪个工作流版本（用于灰度追踪）
        migrations.AddField(
            model_name='project',
            name='gray_flow_version',
            field=models.CharField(
                blank=True, default='',
                help_text='记录创作请求命中的工作流 pack version，用于灰度流量分析',
                max_length=64, verbose_name='命中工作流版本',
            ),
        ),
    ]
