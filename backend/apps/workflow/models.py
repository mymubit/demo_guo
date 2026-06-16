# -*- coding: utf-8 -*-
"""流程中心数据模型 — db_table 与 skill app 迁态前一致。"""
from __future__ import annotations

import uuid

from django.db import models


class FusionJsonSchema(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schema_key = models.CharField("Schema 键", max_length=128, unique=True, db_index=True)
    filename = models.CharField("文件名", max_length=128)
    schema_json = models.JSONField("Schema JSON")
    pack = models.ForeignKey(
        "FusionPipelinePack",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="schemas",
        verbose_name="所属配置包",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "skill_fusion_json_schema"
        verbose_name = "融合 JSON Schema"
        verbose_name_plural = verbose_name
        ordering = ["schema_key"]

    def __str__(self):
        return self.schema_key


class FusionPipelinePack(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField("技能版本", max_length=64, unique=True, db_index=True)
    display_name = models.CharField("展示名称", max_length=128, blank=True, default="")
    description = models.TextField("说明", blank=True, default="")
    slug = models.SlugField("标识", max_length=64, unique=True, null=True, blank=True)
    is_active = models.BooleanField("当前编辑中", default=False, db_index=True)
    is_published_to_portal = models.BooleanField("创作入口可选", default=False, db_index=True)
    is_default_for_creation = models.BooleanField("创作默认流水线", default=False, db_index=True)
    flow_graph = models.JSONField("流程图画布", default=dict, blank=True)
    post_script_chain = models.JSONField("后处理 Agent 链", default=list, blank=True)
    terminal_node_ids = models.JSONField("终止节点 ID 列表", default=list, blank=True)
    project_meta = models.JSONField("projectMeta 快照", default=dict, blank=True)
    imported_from_root = models.CharField("导入来源路径", max_length=512, blank=True, default="")
    notes = models.CharField("备注", max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "skill_fusion_pipeline_pack"
        verbose_name = "融合流水线配置包"
        verbose_name_plural = verbose_name
        ordering = ["-updated_at"]

    def __str__(self):
        label = self.display_name or self.version
        flags = []
        if self.is_active:
            flags.append("编辑中")
        if self.is_published_to_portal:
            flags.append("已发布")
        if self.is_default_for_creation:
            flags.append("默认")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        return f"{label}{suffix}"


class FusionPipelineNode(models.Model):
    RUNNER_FUSION_NODE = "fusion_node"
    RUNNER_FUSION_REVIEW = "fusion_review"
    RUNNER_FUSION_SCORE = "fusion_score"
    RUNNER_AGENT_CHAIN = "agent_chain"
    RUNNER_TYPE_CHOICES = [
        (RUNNER_FUSION_NODE, "融合主链节点"),
        (RUNNER_FUSION_REVIEW, "融合质检"),
        (RUNNER_FUSION_SCORE, "融合评分"),
        (RUNNER_AGENT_CHAIN, "Agent 后处理链"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pack = models.ForeignKey(
        FusionPipelinePack,
        on_delete=models.CASCADE,
        related_name="nodes",
        verbose_name="配置包",
    )
    fusion_node_id = models.CharField("融合节点 ID", max_length=64, db_index=True)
    chain_order = models.PositiveSmallIntegerField("主链顺序")
    website_index = models.PositiveSmallIntegerField("网站步骤序号")
    name = models.CharField("节点名称", max_length=128)
    description = models.TextField("说明", blank=True, default="")
    runner_type = models.CharField(
        "执行器类型",
        max_length=32,
        choices=RUNNER_TYPE_CHOICES,
        blank=True,
        default="",
    )
    runner_path = models.CharField("执行函数路径", max_length=255, blank=True, default="")
    output_key = models.CharField("产物键 outputKey", max_length=64, blank=True, default="")
    artifact_key = models.CharField("存储 artifact_key", max_length=64, blank=True, default="")
    pipeline_result_key = models.CharField("pipeline_result 键", max_length=64, blank=True, default="")
    extra_artifact_keys = models.JSONField("额外 artifact_key 列表", default=list, blank=True)
    schema = models.ForeignKey(
        FusionJsonSchema,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pipeline_nodes",
        verbose_name="JSON Schema",
    )
    is_terminal = models.BooleanField("终止节点", default=False)
    fusion_status = models.CharField("项目状态映射", max_length=32, blank=True, default="")
    enabled = models.BooleanField("启用", default=True)
    requires_confirm = models.BooleanField("分步需确认", default=True)
    portal_visible = models.BooleanField("C 端展示", default=True)
    coin_cost = models.PositiveIntegerField("单步币价", default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "skill_fusion_pipeline_node"
        verbose_name = "融合流水线节点"
        verbose_name_plural = verbose_name
        ordering = ["chain_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["pack", "fusion_node_id"],
                name="uniq_fusion_pack_node_id",
            ),
            models.UniqueConstraint(
                fields=["pack", "chain_order"],
                name="uniq_fusion_pack_chain_order",
            ),
        ]

    def __str__(self):
        return f"{self.website_index}. {self.name} ({self.fusion_node_id})"
