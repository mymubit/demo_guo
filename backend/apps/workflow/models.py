# -*- coding: utf-8 -*-
"""流程中心数据模型 — db_table 与 skill app 迁态前一致。"""
from __future__ import annotations

import uuid

from django.db import models


class WorkflowTemplate(models.Model):
    """工作流模板库

    预置短剧创作标准模板，支持运营/管理员克隆自定义。
    与 FusionPipelinePack 的关系：
    - WorkflowTemplate：模板定义（静态，供克隆）
    - FusionPipelinePack：运行时工作流包（动态，带版本管理）
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_id = models.CharField(
        "模板 ID", max_length=64, unique=True, db_index=True,
        help_text="如 tpl_standard_24ep / tpl_quick_1min",
    )
    name        = models.CharField("模板名称", max_length=128)
    description = models.TextField("模板说明", blank=True, default="")
    nodes       = models.JSONField(
        "节点配置", default=list,
        help_text="数组，每项描述一个工作流节点（agent_id/node_type/config 等）",
    )
    is_system   = models.BooleanField(
        "系统预置", default=False,
        help_text="True=系统预置模板（不可删除）；False=用户/运营自定义",
    )
    created_by  = models.CharField("创建人", max_length=128, blank=True, default="system")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workflow_template"
        verbose_name = "工作流模板"
        verbose_name_plural = verbose_name
        ordering = ["-is_system", "name"]

    def __str__(self):
        tag = "系统" if self.is_system else "自定义"
        return f"[{tag}] {self.name}（{self.template_id}）"


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
    # 工作流版本发布状态
    PACK_DRAFT    = "draft"
    PACK_ACTIVE   = "active"
    PACK_GRAY     = "gray"
    PACK_ARCHIVED = "archived"

    PACK_STATUS_CHOICES = [
        (PACK_DRAFT,    "草稿"),
        (PACK_ACTIVE,   "全量发布"),
        (PACK_GRAY,     "灰度"),
        (PACK_ARCHIVED, "已归档"),
    ]

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

    # 版本管理扩展字段
    pack_status = models.CharField(
        "发布状态", max_length=16, choices=PACK_STATUS_CHOICES,
        default=PACK_DRAFT, db_index=True,
        help_text="draft=草稿；active=全量发布；gray=灰度；archived=已归档",
    )
    gray_weight = models.PositiveSmallIntegerField(
        "灰度权重", default=100,
        help_text="0-100，pack_status=gray 时按此比例分流新创作项目",
    )
    change_notes = models.TextField("变更说明", blank=True, default="")
    published_by = models.CharField(
        "发布人", max_length=128, blank=True, default="",
        help_text="记录发布操作人用户名",
    )
    published_at = models.DateTimeField("发布时间", null=True, blank=True)
    rollback_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="rollback_targets", verbose_name="回滚目标包",
        help_text="标记此包为某次回滚操作的目标版本",
    )

    # 新增：灰度分流稳定哈希种子
    gray_traffic_salt = models.CharField(
        "灰度分流种子", max_length=32, blank=True, default="",
        help_text="用于 gray_traffic_salt + user_id % 100 < gray_weight 稳定分流",
    )
    # 新增：声明该流水线依赖的最低 LLM 配置版本
    min_llm_provider_version = models.CharField(
        "最低 LLM Provider 版本", max_length=64, blank=True, default="",
        help_text="用于兼容性校验，低于此版本拒绝使用此流水线",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "skill_fusion_pipeline_pack"
        verbose_name = "融合流水线配置包"
        verbose_name_plural = verbose_name
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["pack_status", "gray_weight"], name="pack_status_gray_idx"),
        ]

    def __str__(self):
        label = self.display_name or self.version
        flags = []
        if self.pack_status != self.PACK_DRAFT:
            flags.append(self.get_pack_status_display())
        if self.is_default_for_creation:
            flags.append("默认")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        return f"{label}{suffix}"

    def publish(self, *, gray_weight: int = 100, published_by: str = "") -> None:
        """发布工作流包：设置状态为 active 或 gray"""
        from django.utils import timezone
        target = self.PACK_GRAY if gray_weight < 100 else self.PACK_ACTIVE
        self.pack_status = target
        self.gray_weight = gray_weight
        self.published_by = published_by
        self.published_at = timezone.now()
        self.save(update_fields=["pack_status", "gray_weight", "published_by", "published_at", "updated_at"])


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
