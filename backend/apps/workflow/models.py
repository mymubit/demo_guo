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

    # ━━━━ 新增（P0）：编排引擎元数据 ━━━━
    engine_config = models.JSONField(
        "引擎配置", default=dict, blank=True,
        help_text="""编排引擎全局配置示例:
{
  "mode": "async_celery",                 // async_celery | async_thread | sync_debug
  "timeout_seconds": 3600,                // 工作流整体超时
  "max_retries": 3,                       // 默认节点重试次数
  "failure_strategy": "fail_fast",        // fail_fast | continue_on_failure
  "context_retention_days": 30,           // 上下文保留天数
  "allow_parallel": true,                 // 是否允许并行组调度
  "max_parallel_per_group": 5,            // 单并行组最大并发数
  "heartbeat_interval_seconds": 60        // 心跳频率
}""",
    )

    parent_version = models.CharField(
        "父版本追踪", max_length=64, blank=True, default="",
        help_text="记录此版本从哪个版本克隆/升级，支持版本间差异对比",
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
    # P1 阶段扩展：支持并行/迭代/人工门控三类编排节点
    RUNNER_PARALLEL_GROUP = "parallel_group"
    RUNNER_ITERATE_LOOP = "iterate_loop"
    RUNNER_HUMAN_GATE = "human_gate"
    RUNNER_TYPE_CHOICES = [
        (RUNNER_FUSION_NODE, "融合主链节点"),
        (RUNNER_PARALLEL_GROUP, "并行节点组（同级并发）"),
        (RUNNER_ITERATE_LOOP, "迭代循环节点"),
        (RUNNER_HUMAN_GATE, "人工门控节点（分步确认）"),
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
    skill_id = models.CharField(
        "技能 ID", max_length=128, blank=True, default="", db_index=True,
        help_text="用于 SkillBridge 路由。例：creation.brief / fusion.skill.review",
    )
    output_key = models.CharField("产物键 outputKey", max_length=64, blank=True, default="")
    artifact_key = models.CharField("存储 artifact_key", max_length=64, blank=True, default="")
    pipeline_result_key = models.CharField("pipeline_result 键", max_length=64, blank=True, default="")
    extra_artifact_keys = models.JSONField("额外 artifact_key 列表", default=list, blank=True)
    # P1 阶段新增：节点扩展配置（用于 PARALLEL/ITERATE/HUMAN 等高级节点的配置）
    # - parallel_group: {"parallel_group_key": "ep_outline_batch"}
    # - iterate_loop:   {"iterate_max_attempts": 3,
    #                    "iterate_until_condition": {"field": "overall_score", "operator": ">=", "value": 70},
    #                    "iterate_target_node_id": "node-3-outline"}
    # - human_gate:     {"human_gate_message": "请确认大纲后再继续"}
    extra_config = models.JSONField(
        "节点扩展配置", default=dict, blank=True,
        help_text="用于 PARALLEL/ITERATE/HUMAN 节点的差异化配置，结构见字段说明",
    )

    # ━━━━ 新增（P0）：节点依赖与路由声明 ━━━━
    upstream_deps = models.JSONField(
        "上游依赖", default=list, blank=True,
        help_text="依赖的上游 fusion_node_id 列表，例: ['node-brief', 'node-structure']。"
                  "引擎将按依赖关系决定调度顺序，替代原有的 chain_order 硬编码依赖",
    )
    downstream_map = models.JSONField(
        "下游路由映射", default=list, blank=True,
        help_text="本节点成功后的可选中转目标，支持条件分支。结构:"
                  "[{target: 'node_b_id', condition_expr: 'ctx.field > 70', weight: 100}]。"
                  "空列表时由引擎按全局 DAG 选择下一节点。",
    )

    # ━━━━ 新增（P0）：运行时配置（重试/超时/检查点等）━━━━
    runtime_config = models.JSONField(
        "运行时配置", default=dict, blank=True,
        help_text="""示例:
{
  "timeout_seconds": 600,
  "retry_policy": {
    "max_retries": 3,
    "backoff": "exponential",       // exponential | fixed | linear
    "base_seconds": 2
  },
  "coin_cost_override": null,
  "allow_skip": true,
  "is_checkpoint": true,
  "human_gate_required": false,
  "max_context_bytes": 2097152,
  "idempotency_scope": "node"        // node | instance | global
}""",
    )

    # ━━━━ 新增（P0）：执行条件表达式（决定该节点是否真正被执行）━━━━
    condition_expr = models.TextField(
        "执行条件表达式", blank=True, default="",
        help_text="Python 安全表达式，返回 bool。可用变量：ctx（全局上下文）、"
                  "prev（上一节点输出）、nodes（所有已完成节点输出 dict）。"
                  "例：ctx.review_score < 70 或 nodes['node_brief']['is_ok']",
    )
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

