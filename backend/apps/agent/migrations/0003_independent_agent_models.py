from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0002_llm_router_rules"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgentDefinition",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("agent_id", models.CharField(db_index=True, max_length=64, unique=True, verbose_name="Agent ID")),
                ("name", models.CharField(max_length=128, verbose_name="英文名称")),
                ("name_zh", models.CharField(blank=True, default="", max_length=128, verbose_name="中文名称")),
                ("description", models.TextField(blank=True, default="", verbose_name="职责说明")),
                ("category", models.CharField(blank=True, default="creation", max_length=64, verbose_name="分类")),
                ("workspace_order", models.IntegerField(blank=True, db_index=True, null=True, verbose_name="工作台排序")),
                ("is_enabled", models.BooleanField(db_index=True, default=True, verbose_name="启用")),
                ("is_system", models.BooleanField(default=True, verbose_name="系统内置")),
                ("version", models.CharField(default="v1", max_length=32, verbose_name="版本")),
                ("lifecycle_status", models.CharField(choices=[("draft", "草稿"), ("active", "启用"), ("disabled", "停用"), ("archived", "归档")], db_index=True, default="draft", max_length=16, verbose_name="生命周期")),
                ("default_output_artifact_key", models.CharField(blank=True, default="", max_length=64, verbose_name="默认产物键")),
                ("input_contract", models.JSONField(blank=True, default=dict, verbose_name="输入契约")),
                ("output_contract", models.JSONField(blank=True, default=dict, verbose_name="输出契约")),
                ("runtime_policy", models.JSONField(blank=True, default=dict, verbose_name="运行策略")),
                ("ui_schema", models.JSONField(blank=True, default=dict, verbose_name="UI Schema")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Agent 定义",
                "verbose_name_plural": "Agent 定义",
                "db_table": "agent_definition",
                "ordering": ["workspace_order", "agent_id"],
            },
        ),
        migrations.CreateModel(
            name="AgentKnowledgeItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("knowledge_id", models.CharField(db_index=True, max_length=128, unique=True, verbose_name="知识 ID")),
                ("title", models.CharField(max_length=255, verbose_name="标题")),
                ("category", models.CharField(choices=[("rule", "规则"), ("knowledge", "知识"), ("example", "示例"), ("schema", "Schema"), ("validator", "校验器"), ("prompt_section", "Prompt 片段"), ("reference_script", "参考剧本"), ("checklist", "检查清单")], db_index=True, max_length=32, verbose_name="分类")),
                ("source_origin", models.CharField(blank=True, default="", max_length=64, verbose_name="来源")),
                ("source_path", models.CharField(blank=True, default="", max_length=500, verbose_name="来源路径")),
                ("content_text", models.TextField(blank=True, default="", verbose_name="文本内容")),
                ("content_json", models.JSONField(blank=True, default=dict, verbose_name="JSON 内容")),
                ("tags", models.JSONField(blank=True, default=list, verbose_name="标签")),
                ("applies_to_agents", models.JSONField(blank=True, default=list, verbose_name="适用 Agent")),
                ("priority", models.IntegerField(default=100, verbose_name="优先级")),
                ("is_enabled", models.BooleanField(db_index=True, default=True, verbose_name="启用")),
                ("version", models.CharField(default="v1", max_length=32, verbose_name="版本")),
                ("checksum", models.CharField(blank=True, db_index=True, default="", max_length=128, verbose_name="Checksum")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Agent 知识项",
                "verbose_name_plural": "Agent 知识项",
                "db_table": "agent_knowledge_item",
                "ordering": ["category", "priority", "knowledge_id"],
            },
        ),
        migrations.AddField(
            model_name="agentllmrouteconfig",
            name="agent",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="model_routes", to="agent.agentdefinition", verbose_name="Agent"),
        ),
        migrations.AddField(
            model_name="agentllmrouteconfig",
            name="cost_budget_hard",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="硬预算"),
        ),
        migrations.AddField(
            model_name="agentllmrouteconfig",
            name="cost_budget_soft",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="软预算"),
        ),
        migrations.AddField(
            model_name="agentllmrouteconfig",
            name="max_completion_tokens",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Completion Token 上限"),
        ),
        migrations.AddField(
            model_name="agentllmrouteconfig",
            name="max_prompt_tokens",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Prompt Token 上限"),
        ),
        migrations.AddField(
            model_name="agentllmrouteconfig",
            name="temperature",
            field=models.FloatField(blank=True, null=True, verbose_name="温度"),
        ),
        migrations.AddField(
            model_name="agentllmrouteconfig",
            name="timeout_seconds",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="超时秒数"),
        ),
        migrations.CreateModel(
            name="AgentPromptVersion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("version", models.CharField(max_length=32, verbose_name="版本")),
                ("system_prompt", models.TextField(blank=True, default="", verbose_name="System Prompt")),
                ("user_prompt_template", models.TextField(blank=True, default="", verbose_name="User Prompt 模板")),
                ("output_format_prompt", models.TextField(blank=True, default="", verbose_name="输出格式 Prompt")),
                ("constraints_prompt", models.TextField(blank=True, default="", verbose_name="约束 Prompt")),
                ("few_shot_examples", models.JSONField(blank=True, default=list, verbose_name="Few-shot 示例")),
                ("is_active", models.BooleanField(db_index=True, default=False, verbose_name="当前启用")),
                ("change_notes", models.TextField(blank=True, default="", verbose_name="变更说明")),
                ("created_by", models.CharField(blank=True, default="", max_length=128, verbose_name="创建人")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("agent", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="prompt_versions", to="agent.agentdefinition", verbose_name="Agent")),
            ],
            options={
                "verbose_name": "Agent Prompt 版本",
                "verbose_name_plural": "Agent Prompt 版本",
                "db_table": "agent_prompt_version",
                "ordering": ["agent__agent_id", "-created_at"],
                "unique_together": {("agent", "version")},
            },
        ),
        migrations.CreateModel(
            name="AgentKnowledgeBinding",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("binding_type", models.CharField(choices=[("required", "必需"), ("optional", "可选"), ("fallback", "兜底"), ("validator", "校验器"), ("output_schema", "输出 Schema")], max_length=32, verbose_name="绑定类型")),
                ("inject_position", models.CharField(choices=[("system", "System"), ("user", "User"), ("context", "Context"), ("validator", "Validator")], max_length=32, verbose_name="注入位置")),
                ("order_index", models.IntegerField(default=0, verbose_name="排序")),
                ("max_chars", models.PositiveIntegerField(blank=True, null=True, verbose_name="最大注入字符数")),
                ("condition_expr", models.CharField(blank=True, default="", max_length=255, verbose_name="条件表达式")),
                ("is_enabled", models.BooleanField(db_index=True, default=True, verbose_name="启用")),
                ("agent", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="knowledge_bindings", to="agent.agentdefinition", verbose_name="Agent")),
                ("knowledge", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="agent_bindings", to="agent.agentknowledgeitem", verbose_name="知识项")),
            ],
            options={
                "verbose_name": "Agent 知识绑定",
                "verbose_name_plural": "Agent 知识绑定",
                "db_table": "agent_knowledge_binding",
                "ordering": ["agent__agent_id", "order_index", "knowledge__priority"],
                "unique_together": {("agent", "knowledge", "binding_type", "inject_position")},
            },
        ),
        migrations.AddIndex(
            model_name="agentdefinition",
            index=models.Index(fields=["lifecycle_status", "is_enabled"], name="agent_defin_lifecyc_c73289_idx"),
        ),
        migrations.AddIndex(
            model_name="agentdefinition",
            index=models.Index(fields=["category", "workspace_order"], name="agent_defin_categor_6f1aa4_idx"),
        ),
        migrations.AddIndex(
            model_name="agentknowledgeitem",
            index=models.Index(fields=["category", "is_enabled"], name="agent_knowl_categor_774375_idx"),
        ),
        migrations.AddIndex(
            model_name="agentknowledgeitem",
            index=models.Index(fields=["source_origin", "checksum"], name="agent_knowl_source__7b708e_idx"),
        ),
        migrations.AddConstraint(
            model_name="agentpromptversion",
            constraint=models.UniqueConstraint(condition=models.Q(("is_active", True)), fields=("agent",), name="uniq_active_prompt_per_agent"),
        ),
    ]
