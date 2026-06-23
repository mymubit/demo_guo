# -*- coding: utf-8 -*-
# Generated migration: operations 运营监控中心
# - CreationFeedback 用户反馈
# - OperationsDailyCache 聚合缓存

import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('creation', '0016_project_content_quality_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CreationFeedback',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('category', models.CharField(
                    choices=[
                        ('feature_request', '功能建议'),
                        ('bug', 'BUG 报告'),
                        ('consult', '使用咨询'),
                        ('praise', '表扬'),
                        ('complaint', '投诉'),
                        ('other', '其它'),
                    ],
                    db_index=True, default='feature_request', max_length=24, verbose_name='分类',
                )),
                ('severity', models.CharField(
                    choices=[
                        ('P0', 'P0 紧急（影响创作主链路）'),
                        ('P1', 'P1 高（影响 1 个节点）'),
                        ('P2', 'P2 中（体验问题）'),
                        ('P3', 'P3 低（建议性）'),
                    ],
                    db_index=True, default='P2', max_length=4, verbose_name='严重程度',
                )),
                ('source', models.CharField(
                    choices=[
                        ('workspace', '工作台'),
                        ('portal', 'C 端门户'),
                        ('admin_import', '后台导入'),
                        ('quality_sample', '运营抽样'),
                        ('wechat', '微信群'),
                        ('phone', '电话'),
                    ],
                    db_index=True, default='workspace', max_length=24, verbose_name='来源',
                )),
                ('status', models.CharField(
                    choices=[
                        ('open', '待处理'),
                        ('in_progress', '处理中'),
                        ('resolved', '已处理'),
                        ('wont_fix', '不处理'),
                    ],
                    db_index=True, default='open', max_length=16, verbose_name='状态',
                )),
                ('title', models.CharField(max_length=200, verbose_name='标题')),
                ('content', models.TextField(blank=True, default='', verbose_name='反馈正文')),
                ('contact', models.CharField(blank=True, default='', max_length=120, verbose_name='联系方式')),
                ('tags', models.JSONField(blank=True, default=list, verbose_name='标签')),
                ('handled_at', models.DateTimeField(blank=True, null=True, verbose_name='处理时间')),
                ('handler_note', models.TextField(blank=True, default='', verbose_name='处理备注')),
                ('is_from_sample', models.BooleanField(db_index=True, default=False, verbose_name='来自抽样')),
                ('created_at', models.DateTimeField(db_index=True, default=__import__('django.utils.timezone', fromlist=['now']).now, verbose_name='提交时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('handler', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.SET_NULL,
                    related_name='handled_creation_feedbacks',
                    to=settings.AUTH_USER_MODEL, verbose_name='处理人',
                )),
                ('project', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.SET_NULL,
                    related_name='feedbacks',
                    to='creation.project', verbose_name='关联项目',
                )),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.SET_NULL,
                    related_name='creation_feedbacks',
                    to=settings.AUTH_USER_MODEL, verbose_name='提交人',
                )),
            ],
            options={
                'verbose_name': '用户反馈',
                'verbose_name_plural': '用户反馈',
                'db_table': 'operations_creation_feedback',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='creationfeedback',
            index=models.Index(fields=['status', '-created_at'], name='cfb_status_time_idx'),
        ),
        migrations.AddIndex(
            model_name='creationfeedback',
            index=models.Index(fields=['category', '-created_at'], name='cfb_category_time_idx'),
        ),
        migrations.AddIndex(
            model_name='creationfeedback',
            index=models.Index(fields=['severity', 'status'], name='cfb_sev_status_idx'),
        ),
        migrations.AddIndex(
            model_name='creationfeedback',
            index=models.Index(fields=['user', '-created_at'], name='cfb_user_time_idx'),
        ),
        migrations.CreateModel(
            name='OperationsDailyCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cache_date', models.DateField(db_index=True, verbose_name='缓存日期')),
                ('metric_type', models.CharField(
                    choices=[
                        ('dashboard', '总 Dashboard'),
                        ('content_quality', '内容质量'),
                        ('feedback', '反馈汇总'),
                        ('config_hit', '配置命中率'),
                        ('funnel', '用户漏斗'),
                    ],
                    db_index=True, max_length=32, verbose_name='指标类型',
                )),
                ('payload', models.JSONField(blank=True, default=dict, verbose_name='聚合数据')),
                ('extra', models.JSONField(blank=True, default=dict, verbose_name='扩展')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '运营聚合缓存',
                'verbose_name_plural': '运营聚合缓存',
                'db_table': 'operations_daily_cache',
                'ordering': ['-cache_date', 'metric_type'],
            },
        ),
        migrations.AddConstraint(
            model_name='operationsdailycache',
            constraint=models.UniqueConstraint(
                fields=('cache_date', 'metric_type'),
                name='uniq_ops_daily_cache',
            ),
        ),
        migrations.AddIndex(
            model_name='operationsdailycache',
            index=models.Index(fields=['metric_type', '-cache_date'], name='ops_cache_metric_date_idx'),
        ),
        # UserBehaviorEvent 6 个核心用户行为埋点
        migrations.CreateModel(
            name='UserBehaviorEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_name', models.CharField(
                    choices=[
                        ('landing_view', '落地页访问'),
                        ('creation_form_open', '打开创作表单'),
                        ('creation_submitted', '提交创作'),
                        ('node_edited', '编辑节点'),
                        ('script_exported', '导出剧本'),
                        ('share_link_generated', '生成分享链接'),
                    ],
                    db_index=True, max_length=48, verbose_name='事件名',
                )),
                ('source', models.CharField(
                    choices=[('frontend', '前端'), ('backend', '后端')],
                    db_index=True, default='frontend', max_length=16, verbose_name='来源',
                )),
                ('session_id', models.CharField(blank=True, default='', db_index=True, max_length=64, verbose_name='会话ID')),
                ('project_id', models.CharField(blank=True, default='', db_index=True, max_length=64, verbose_name='项目ID')),
                ('page', models.CharField(blank=True, default='', max_length=200, verbose_name='页面/路由')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')),
                ('user_agent', models.CharField(blank=True, default='', max_length=512, verbose_name='User-Agent')),
                ('payload', models.JSONField(blank=True, default=dict, verbose_name='载荷')),
                ('created_at', models.DateTimeField(db_index=True, default=__import__('django.utils.timezone', fromlist=['now']).now, verbose_name='发生时间')),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.SET_NULL,
                    related_name='behavior_events',
                    to=settings.AUTH_USER_MODEL, verbose_name='用户',
                )),
            ],
            options={
                'verbose_name': '用户行为事件',
                'verbose_name_plural': '用户行为事件',
                'db_table': 'operations_user_behavior_event',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='userbehaviorevent',
            index=models.Index(fields=['event_name', '-created_at'], name='ube_name_time_idx'),
        ),
        migrations.AddIndex(
            model_name='userbehaviorevent',
            index=models.Index(fields=['user', '-created_at'], name='ube_user_time_idx'),
        ),
        migrations.AddIndex(
            model_name='userbehaviorevent',
            index=models.Index(fields=['session_id', '-created_at'], name='ube_session_time_idx'),
        ),
        migrations.AddIndex(
            model_name='userbehaviorevent',
            index=models.Index(fields=['project_id', '-created_at'], name='ube_project_time_idx'),
        ),
    ]
