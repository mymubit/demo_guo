# Generated migration: Project 内容质量统计字段（运营 M2）
# 新增 user_edit_count / final_export_count / last_edited_at / abandoned_at / is_quality_sampled

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creation', '0015_project_gray_flow_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='user_edit_count',
            field=models.PositiveIntegerField(
                default=0,
                help_text='用户在工作台内对 Project 的手动编辑次数（保存草稿节点+1）',
                verbose_name='用户编辑次数',
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='final_export_count',
            field=models.PositiveIntegerField(
                default=0,
                help_text='用户从工作台成功下载/导出最终剧本的次数',
                verbose_name='最终导出次数',
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='last_edited_at',
            field=models.DateTimeField(
                blank=True, null=True,
                help_text='用户最近一次编辑时间；超过 7 天未编辑+未完成=潜在弃用',
                verbose_name='最近编辑时间',
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='abandoned_at',
            field=models.DateTimeField(
                blank=True, db_index=True, null=True,
                help_text='用户主动放弃或超过 7 天未活跃即视为弃用；用于运营漏斗/质量分析',
                verbose_name='弃用时间',
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='is_quality_sampled',
            field=models.BooleanField(
                db_index=True, default=False,
                help_text='运营分析/反馈抽样的标记位，避免重复抽样',
                verbose_name='已采样分析',
            ),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['abandoned_at', 'status'], name='proj_abandon_status_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['-created_at', 'status'], name='proj_created_status_idx'),
        ),
    ]
