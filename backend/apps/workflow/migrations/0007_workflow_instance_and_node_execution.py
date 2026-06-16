# P0 阶段：为 FusionPipelinePack + FusionPipelineNode 补充引擎所需字段，
# 并新增工作流执行实例表（WorkflowInstance / NodeExecution / NodeExecutionEvent）。
#
# 字段说明：
#   - Pack.engine_config / Pack.parent_version：支持灰度/版本/新引擎配置；
#   - Node.upstream_deps / downstream_map / runtime_config / condition_expr：
#     支持以节点级的依赖声明、条件路由、重试/超时、跳过规则；
#   - 新建三张表（见底部）：工作流实例、节点级执行记录、事件日志。

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0006_fusionpipelinenode_extra_config'),
    ]

    operations = [
        # ── FusionPipelinePack：engine_config / parent_version ──
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='engine_config',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    '编排引擎全局配置（灰度/超时/最大重试/并行/心跳等，'
                    '详见 WorkflowEngine 注释中的字段说明'
                ),
                verbose_name='引擎配置',
            ),
        ),
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='parent_version',
            field=models.CharField(
                blank=True,
                default='',
                help_text='记录此工作流包从哪个版本克隆/升级，便于版本间差异对比',
                max_length=64,
                verbose_name='父版本追踪',
            ),
        ),

        # ── FusionPipelineNode：四字段 ──
        migrations.AddField(
            model_name='fusionpipelinenode',
            name='upstream_deps',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    '依赖的上游 fusion_node_id 列表，引擎据此构建 DAG。'
                    '空列表时回退使用 chain_order。'
                ),
                verbose_name='上游依赖',
            ),
        ),
        migrations.AddField(
            model_name='fusionpipelinenode',
            name='downstream_map',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    '本节点成功后的可选下游路由列表，支持条件分支。'
                    '结构：[{"target":"node_xxx","condition_expr":"...","weight":100}]'
                ),
                verbose_name='下游路由映射',
            ),
        ),
        migrations.AddField(
            model_name='fusionpipelinenode',
            name='runtime_config',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    '节点运行时配置：timeout_seconds、retry_policy（max_retries/backoff/base_seconds）、'
                    'coin_cost_override、allow_skip、is_checkpoint、human_gate_required、'
                    'max_context_bytes、idempotency_scope'
                ),
                verbose_name='运行时配置',
            ),
        ),
        migrations.AddField(
            model_name='fusionpipelinenode',
            name='condition_expr',
            field=models.TextField(
                blank=True,
                default='',
                help_text=(
                    'Python 安全表达式，返回 bool。为空视为通过。'
                    '可访问 ctx/nodes/prev/constants。例：ctx.review_score < 70'
                ),
                verbose_name='执行条件表达式',
            ),
        ),

        # ── 新增三张表 ──
        migrations.CreateModel(
            name='WorkflowInstance',
            fields=[
                ('id', models.UUIDField(
                    default=models.NOT_PROVIDED, editable=False, primary_key=True,
                    serialize=False,
                )),
                ('user_id', models.CharField(
                    blank=True, default='', max_length=128, verbose_name='触发用户',
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', '待执行'),
                        ('running', '运行中'),
                        ('paused', '已暂停'),
                        ('waiting_human', '等待人工确认'),
                        ('done', '成功'),
                        ('failed', '失败'),
                        ('cancelled', '已取消'),
                    ],
                    default='pending', max_length=16, verbose_name='状态', db_index=True,
                )),
                ('current_node_id', models.CharField(
                    blank=True, default='', max_length=64, verbose_name='当前节点',
                )),
                ('context', models.JSONField(
                    blank=True, default=dict, verbose_name='执行上下文快照',
                )),
                ('started_at', models.DateTimeField(
                    blank=True, null=True, verbose_name='开始时间',
                )),
                ('finished_at', models.DateTimeField(
                    blank=True, null=True, verbose_name='结束时间',
                )),
                ('last_heartbeat_at', models.DateTimeField(
                    blank=True, null=True, verbose_name='最近心跳', db_index=True,
                )),
                ('total_duration_ms', models.PositiveIntegerField(
                    default=0, verbose_name='总耗时(ms)',
                )),
                ('failure_reason', models.TextField(
                    blank=True, default='', verbose_name='失败原因',
                )),
                ('failure_node_id', models.CharField(
                    blank=True, default='', max_length=64, verbose_name='失败节点',
                )),
                ('trigger_type', models.CharField(
                    choices=[
                        ('user', '用户触发'), ('api', 'API 调用'),
                        ('retry', '重试'), ('rollback', '回滚'),
                    ],
                    default='user', max_length=16, db_index=True,
                )),
                ('start_node_id', models.CharField(
                    blank=True, default='', max_length=64, verbose_name='起始节点',
                )),
                ('coin_cost_total', models.PositiveIntegerField(
                    default=0, verbose_name='金币合计',
                )),
                ('llm_token_in_total', models.PositiveIntegerField(
                    default=0, verbose_name='输入Token合计',
                )),
                ('llm_token_out_total', models.PositiveIntegerField(
                    default=0, verbose_name='输出Token合计',
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True, verbose_name='创建时间', db_index=True,
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True, verbose_name='更新时间',
                )),
                ('pack', models.ForeignKey(
                    on_delete=models.deletion.PROTECT,
                    related_name='instances',
                    to='workflow.fusionpipelinepack', verbose_name='工作流包',
                )),
                ('project', models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.CASCADE,
                    related_name='workflow_instances', to='creation.project',
                    verbose_name='关联项目',
                )),
                ('rollback_from_instance', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.SET_NULL,
                    related_name='rollback_children',
                    to='workflow.workflowinstance',
                    verbose_name='回滚自哪个实例',
                )),
            ],
            options={
                'db_table': 'workflow_instance',
                'verbose_name': '工作流执行实例',
                'verbose_name_plural': '工作流执行实例',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['project_id', 'status', '-created_at'],
                                 name='inst_project_status_idx'),
                    models.Index(fields=['pack_id', 'status'],
                                 name='inst_pack_status_idx'),
                    models.Index(fields=['status', 'last_heartbeat_at'],
                                 name='inst_heartbeat_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='NodeExecution',
            fields=[
                ('id', models.UUIDField(
                    default=models.NOT_PROVIDED, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('node_id', models.CharField(
                    max_length=64, verbose_name='节点ID', db_index=True,
                )),
                ('node_name', models.CharField(
                    blank=True, default='', max_length=128,
                    verbose_name='节点名称',
                )),
                ('runner_type', models.CharField(
                    blank=True, default='', max_length=32, verbose_name='节点类型',
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', '待执行'), ('skipped', '条件跳过'),
                        ('running', '运行中'), ('succeeded', '成功'),
                        ('failed', '失败'), ('timed_out', '超时'),
                        ('cancelled', '已取消'),
                    ],
                    default='pending', max_length=16, verbose_name='状态', db_index=True,
                )),
                ('input_context', models.JSONField(
                    blank=True, default=dict, verbose_name='入参上下文',
                )),
                ('output_context', models.JSONField(
                    blank=True, default=dict, verbose_name='出参上下文',
                )),
                ('errors', models.JSONField(
                    blank=True, default=list, verbose_name='错误详情',
                )),
                ('attempt', models.PositiveSmallIntegerField(
                    default=1, verbose_name='第几次尝试',
                )),
                ('max_retries', models.PositiveSmallIntegerField(
                    default=3, verbose_name='最大重试次数',
                )),
                ('coin_cost', models.PositiveIntegerField(
                    default=0, verbose_name='消耗金币',
                )),
                ('llm_token_in', models.PositiveIntegerField(
                    default=0, verbose_name='输入Token',
                )),
                ('llm_token_out', models.PositiveIntegerField(
                    default=0, verbose_name='输出Token',
                )),
                ('started_at', models.DateTimeField(
                    blank=True, null=True, verbose_name='开始时间',
                )),
                ('finished_at', models.DateTimeField(
                    blank=True, null=True, verbose_name='完成时间',
                )),
                ('duration_ms', models.PositiveIntegerField(
                    default=0, verbose_name='耗时(ms)',
                )),
                ('agent_execution_run_ids', models.JSONField(
                    blank=True, default=list,
                    verbose_name='关联Agent执行记录ID',
                )),
                ('idempotency_key', models.CharField(
                    blank=True, default='', max_length=128, unique=True,
                    verbose_name='幂等键',
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True, verbose_name='创建时间', db_index=True,
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True, verbose_name='更新时间',
                )),
                ('instance', models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name='node_executions',
                    to='workflow.workflowinstance',
                    verbose_name='所属实例',
                )),
            ],
            options={
                'db_table': 'workflow_node_execution',
                'verbose_name': '节点执行记录',
                'verbose_name_plural': '节点执行记录',
                'ordering': ['instance_id', 'created_at'],
                'indexes': [
                    models.Index(fields=['instance_id', 'node_id', 'status'],
                                 name='ne_inst_node_status_idx'),
                    models.Index(fields=['status', '-created_at'],
                                 name='ne_status_created_idx'),
                    models.Index(fields=['instance_id', 'attempt'],
                                 name='ne_inst_attempt_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='NodeExecutionEvent',
            fields=[
                ('id', models.UUIDField(
                    default=models.NOT_PROVIDED, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('event_type', models.CharField(
                    default='generic', max_length=32, verbose_name='事件类型',
                )),
                ('level', models.CharField(
                    choices=[
                        ('info', '信息'), ('warn', '告警'), ('error', '错误'),
                    ],
                    default='info', max_length=8, db_index=True,
                    verbose_name='级别',
                )),
                ('message', models.TextField(
                    blank=True, default='', verbose_name='事件描述',
                )),
                ('duration_ms', models.PositiveIntegerField(
                    default=0, verbose_name='耗时(ms)',
                )),
                ('extra', models.JSONField(
                    blank=True, default=dict, verbose_name='附加数据',
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True, verbose_name='创建时间', db_index=True,
                )),
                ('execution', models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name='events',
                    to='workflow.nodeexecution',
                )),
            ],
            options={
                'db_table': 'workflow_node_execution_event',
                'verbose_name': '节点执行事件',
                'verbose_name_plural': '节点执行事件',
                'ordering': ['created_at'],
            },
        ),
    ]
