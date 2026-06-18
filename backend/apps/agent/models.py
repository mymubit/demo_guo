# -*- coding: utf-8 -*-
"""Agent 中心数据模型 — db_table 与 skill app 迁态前一致。"""
from __future__ import annotations

import uuid

from django.db import models
from django.db.models import Q


class AgentDefinition(models.Model):
    class LifecycleStatus(models.TextChoices):
        DRAFT = "draft", "草稿"
        ACTIVE = "active", "启用"
        DISABLED = "disabled", "停用"
        ARCHIVED = "archived", "归档"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_id = models.CharField("Agent ID", max_length=64, unique=True, db_index=True)
    name = models.CharField("英文名称", max_length=128)
    name_zh = models.CharField("中文名称", max_length=128, blank=True, default="")
    description = models.TextField("职责说明", blank=True, default="")
    category = models.CharField("分类", max_length=64, blank=True, default="creation")
    workspace_order = models.IntegerField("工作台排序", null=True, blank=True, db_index=True)
    is_enabled = models.BooleanField("启用", default=True, db_index=True)
    is_system = models.BooleanField("系统内置", default=True)
    version = models.CharField("版本", max_length=32, default="v1")
    lifecycle_status = models.CharField(
        "生命周期",
        max_length=16,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.DRAFT,
        db_index=True,
    )
    default_output_artifact_key = models.CharField("默认产物键", max_length=64, blank=True, default="")
    input_contract = models.JSONField("输入契约", default=dict, blank=True)
    output_contract = models.JSONField("输出契约", default=dict, blank=True)
    runtime_policy = models.JSONField("运行策略", default=dict, blank=True)
    ui_schema = models.JSONField("UI Schema", default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_definition"
        verbose_name = "Agent 定义"
        verbose_name_plural = verbose_name
        ordering = ["workspace_order", "agent_id"]
        indexes = [
            models.Index(fields=["lifecycle_status", "is_enabled"], name="agent_defin_lifecyc_c73289_idx"),
            models.Index(fields=["category", "workspace_order"], name="agent_defin_categor_6f1aa4_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.agent_id} · {self.name_zh or self.name}"


class AgentPromptVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        AgentDefinition,
        on_delete=models.CASCADE,
        related_name="prompt_versions",
        verbose_name="Agent",
    )
    version = models.CharField("版本", max_length=32)
    system_prompt = models.TextField("System Prompt", blank=True, default="")
    user_prompt_template = models.TextField("User Prompt 模板", blank=True, default="")
    output_format_prompt = models.TextField("输出格式 Prompt", blank=True, default="")
    constraints_prompt = models.TextField("约束 Prompt", blank=True, default="")
    few_shot_examples = models.JSONField("Few-shot 示例", default=list, blank=True)
    is_active = models.BooleanField("当前启用", default=False, db_index=True)
    change_notes = models.TextField("变更说明", blank=True, default="")
    created_by = models.CharField("创建人", max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_prompt_version"
        verbose_name = "Agent Prompt 版本"
        verbose_name_plural = verbose_name
        unique_together = [["agent", "version"]]
        constraints = [
            models.UniqueConstraint(
                fields=["agent"],
                condition=Q(is_active=True),
                name="uniq_active_prompt_per_agent",
            ),
        ]
        ordering = ["agent__agent_id", "-created_at"]

    def __str__(self) -> str:
        return f"{self.agent.agent_id} · {self.version}"


class AgentKnowledgeItem(models.Model):
    class Category(models.TextChoices):
        RULE = "rule", "规则"
        KNOWLEDGE = "knowledge", "知识"
        EXAMPLE = "example", "示例"
        SCHEMA = "schema", "Schema"
        VALIDATOR = "validator", "校验器"
        PROMPT_SECTION = "prompt_section", "Prompt 片段"
        REFERENCE_SCRIPT = "reference_script", "参考剧本"
        CHECKLIST = "checklist", "检查清单"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge_id = models.CharField("知识 ID", max_length=128, unique=True, db_index=True)
    title = models.CharField("标题", max_length=255)
    category = models.CharField("分类", max_length=32, choices=Category.choices, db_index=True)
    source_origin = models.CharField("来源", max_length=64, blank=True, default="")
    source_path = models.CharField("来源路径", max_length=500, blank=True, default="")
    content_text = models.TextField("文本内容", blank=True, default="")
    content_json = models.JSONField("JSON 内容", default=dict, blank=True)
    tags = models.JSONField("标签", default=list, blank=True)
    applies_to_agents = models.JSONField("适用 Agent", default=list, blank=True)
    priority = models.IntegerField("优先级", default=100)
    is_enabled = models.BooleanField("启用", default=True, db_index=True)
    version = models.CharField("版本", max_length=32, default="v1")
    checksum = models.CharField("Checksum", max_length=128, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_knowledge_item"
        verbose_name = "Agent 知识项"
        verbose_name_plural = verbose_name
        ordering = ["category", "priority", "knowledge_id"]
        indexes = [
            models.Index(fields=["category", "is_enabled"], name="agent_knowl_categor_774375_idx"),
            models.Index(fields=["source_origin", "checksum"], name="agent_knowl_source__7b708e_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.knowledge_id} · {self.title}"


class AgentKnowledgeBinding(models.Model):
    class BindingType(models.TextChoices):
        REQUIRED = "required", "必需"
        OPTIONAL = "optional", "可选"
        FALLBACK = "fallback", "兜底"
        VALIDATOR = "validator", "校验器"
        OUTPUT_SCHEMA = "output_schema", "输出 Schema"

    class InjectPosition(models.TextChoices):
        SYSTEM = "system", "System"
        USER = "user", "User"
        CONTEXT = "context", "Context"
        VALIDATOR = "validator", "Validator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        AgentDefinition,
        on_delete=models.CASCADE,
        related_name="knowledge_bindings",
        verbose_name="Agent",
    )
    knowledge = models.ForeignKey(
        AgentKnowledgeItem,
        on_delete=models.CASCADE,
        related_name="agent_bindings",
        verbose_name="知识项",
    )
    binding_type = models.CharField("绑定类型", max_length=32, choices=BindingType.choices)
    inject_position = models.CharField("注入位置", max_length=32, choices=InjectPosition.choices)
    order_index = models.IntegerField("排序", default=0)
    max_chars = models.PositiveIntegerField("最大注入字符数", null=True, blank=True)
    condition_expr = models.CharField("条件表达式", max_length=255, blank=True, default="")
    is_enabled = models.BooleanField("启用", default=True, db_index=True)

    class Meta:
        db_table = "agent_knowledge_binding"
        verbose_name = "Agent 知识绑定"
        verbose_name_plural = verbose_name
        unique_together = [["agent", "knowledge", "binding_type", "inject_position"]]
        ordering = ["agent__agent_id", "order_index", "knowledge__priority"]

    def __str__(self) -> str:
        return f"{self.agent.agent_id} -> {self.knowledge.knowledge_id}"


class AgentLlmRouteConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route_key = models.CharField("路由键", max_length=64, unique=True, db_index=True)
    display_name = models.CharField("展示名称", max_length=128, blank=True, default="")
    agent = models.ForeignKey(
        AgentDefinition,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="model_routes",
        verbose_name="Agent",
    )
    llm_provider = models.ForeignKey(
        "skill.LlmProvider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_llm_routes",
        verbose_name="指定大模型",
    )
    max_tokens = models.PositiveIntegerField("Max Tokens", null=True, blank=True)
    max_prompt_tokens = models.PositiveIntegerField("Prompt Token 上限", null=True, blank=True)
    max_completion_tokens = models.PositiveIntegerField("Completion Token 上限", null=True, blank=True)
    temperature = models.FloatField("温度", null=True, blank=True)
    timeout_seconds = models.PositiveIntegerField("超时秒数", null=True, blank=True)
    cost_budget_soft = models.PositiveIntegerField("软预算", null=True, blank=True)
    cost_budget_hard = models.PositiveIntegerField("硬预算", null=True, blank=True)
    routing_rules = models.JSONField(
        "路由规则 JSON",
        default=dict,
        blank=True,
        help_text=(
            "多维路由规则配置，格式："
            '{"rules":[{"priority":1,'
            '"conditions":{"theme":[],"node_type":[],"user_tier":[],"time_window":{}},'
            '"model_name":"gpt-4o-mini","provider_id":"xxx","cost_score":0}]}'
        ),
    )
    is_active = models.BooleanField("启用", default=True)
    sort_order = models.IntegerField("排序", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agent LLM 路由"
        verbose_name_plural = verbose_name
        db_table = "skill_agent_llm_route"
        ordering = ["sort_order", "route_key"]

    def __str__(self) -> str:
        return f"{self.route_key} · {self.display_name or self.route_key}"


class AgentRegistryConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=64, unique=True, default="default")
    display_name = models.CharField("展示名称", max_length=128, blank=True, default="Agent 注册表")
    registry = models.JSONField("Agent Registry JSON", default=dict, blank=True)
    is_active = models.BooleanField("启用", default=False, db_index=True)
    note = models.CharField("备注", max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agent 注册表配置"
        verbose_name_plural = verbose_name
        db_table = "skill_agent_registry_config"
        ordering = ["-is_active", "config_key"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            AgentRegistryConfig.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    def __str__(self) -> str:
        flag = " [active]" if self.is_active else ""
        return f"{self.display_name or self.config_key}{flag}"


class ReviewScoringConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, unique=True, default="default")
    weights = models.JSONField("维度权重", default=dict, blank=True)
    grade_thresholds = models.JSONField("等级阈值", default=dict, blank=True)
    pass_threshold = models.PositiveSmallIntegerField("通过分数线", default=70)
    min_sub_item_score = models.PositiveSmallIntegerField("子项最低分", default=75)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "质量审查评分"
        verbose_name_plural = verbose_name
        db_table = "skill_review_scoring_config"

    def __str__(self) -> str:
        return f"审查评分 · 通过线 {self.pass_threshold}"
