# -*- coding: utf-8 -*-
"""工作流执行模型
========================================================
WorkflowInstance + NodeExecution — 工作流引擎运行时的持久化锚点。

设计原则：
  ① 与现有 FusionPipelinePack/FusionPipelineNode 松耦合
  ② 所有字段均有安全默认值，允许增量上线（先建表 + 空跑，后实装）
  ③ 状态机严格单一状态字段（status），避免多字段组合判断
  ④ 支持断点续跑：context JSON 保存完整可回放上下文
========================================================
"""
from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from django.db import models


# =========================================================
# WorkflowInstance — 工作流执行实例
# =========================================================
class WorkflowInstance(models.Model):
    """一次创作 = 一个 WorkflowInstance

    生命周期状态机（单一状态字段，非空即合法）：
        pending  → 已创建未开始
        running  → 正在执行
        paused   → 人为暂停/等待人工确认
        waiting_human → 人工门控挂起
        done     → 全流程成功
        failed   → 异常中断（含超时/致命错误）
        cancelled → 主动取消
    """

    STATUS_PENDING       = "pending"
    STATUS_RUNNING       = "running"
    STATUS_PAUSED        = "paused"
    STATUS_WAITING_HUMAN = "waiting_human"
    STATUS_DONE          = "done"
    STATUS_FAILED        = "failed"
    STATUS_CANCELLED     = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING,       "待执行"),
        (STATUS_RUNNING,       "运行中"),
        (STATUS_PAUSED,        "已暂停"),
        (STATUS_WAITING_HUMAN, "等待人工确认"),
        (STATUS_DONE,          "成功"),
        (STATUS_FAILED,        "失败"),
        (STATUS_CANCELLED,     "已取消"),
    ]

    TRIGGER_USER   = "user"
    TRIGGER_API    = "api"
    TRIGGER_RETRY  = "retry"
    TRIGGER_ROLLBACK = "rollback"
    TRIGGER_TYPE_CHOICES = [
        (TRIGGER_USER,     "用户触发"),
        (TRIGGER_API,      "API 调用"),
        (TRIGGER_RETRY,    "重试"),
        (TRIGGER_ROLLBACK, "回滚"),
    ]

    # ── 主键与关联 ───────────────────────────────
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    pack = models.ForeignKey(
        "FusionPipelinePack",
        on_delete=models.PROTECT,  # 运行期间不允许删除 Pack
        related_name="instances",
        verbose_name="工作流包",
    )

    project = models.ForeignKey(
        "creation.Project",
        on_delete=models.CASCADE,
        related_name="workflow_instances",
        null=True, blank=True,
        verbose_name="关联项目",
    )

    user_id = models.CharField(
        "触发用户", max_length=128, blank=True, default="", db_index=True,
    )

    # ── 状态机核心字段 ───────────────────────────
    status = models.CharField(
        "状态", max_length=16, choices=STATUS_CHOICES,
        default=STATUS_PENDING, db_index=True,
    )

    current_node_id = models.CharField(
        "当前节点", max_length=64, blank=True, default="",
        help_text="正在执行/等待执行的 fusion_node_id，用于断点续跑",
    )

    # ── 上下文快照（可回放/可恢复）───────────────
    context = models.JSONField(
        "执行上下文快照", default=dict, blank=True,
        help_text="存各节点的产物输出。键为 artifact_key，"
                  "用于：① 下一节点输入 ② 断点恢复 ③ 执行追溯",
    )

    # ── 时间字段 ─────────────────────────────────
    started_at = models.DateTimeField("开始时间", null=True, blank=True)
    finished_at = models.DateTimeField("结束时间", null=True, blank=True)
    last_heartbeat_at = models.DateTimeField("最近心跳", null=True, blank=True, db_index=True)
    total_duration_ms = models.PositiveIntegerField("总耗时(ms)", default=0)

    # ── 错误与回滚信息 ───────────────────────────
    failure_reason = models.TextField("失败原因", blank=True, default="")
    failure_node_id = models.CharField(
        "失败节点", max_length=64, blank=True, default="",
    )
    rollback_from_instance = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="rollback_children",
        verbose_name="回滚自哪个实例",
    )

    # ── 触发信息 ─────────────────────────────────
    trigger_type = models.CharField(
        "触发方式", max_length=16, default=TRIGGER_USER,
        choices=TRIGGER_TYPE_CHOICES, db_index=True,
    )
    start_node_id = models.CharField(
        "起始节点", max_length=64, blank=True, default="",
        help_text="断点续跑/局部重跑时指定的起始节点；空=从头开始",
    )

    # ── 计费汇总（冗余但方便快速查询）───────────
    coin_cost_total = models.PositiveIntegerField("金币合计", default=0)
    llm_token_in_total = models.PositiveIntegerField("输入Token合计", default=0)
    llm_token_out_total = models.PositiveIntegerField("输出Token合计", default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =====================================================
    # 数据库层配置
    # =====================================================
    class Meta:
        db_table = "workflow_instance"
        verbose_name = "工作流执行实例"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project_id", "status", "-created_at"],
                         name="inst_project_status_idx"),
            models.Index(fields=["pack_id", "status"],
                         name="inst_pack_status_idx"),
            models.Index(fields=["status", "last_heartbeat_at"],
                         name="inst_heartbeat_idx"),
        ]

    def __str__(self) -> str:
        proj = f" · proj={self.project_id[:8]}" if self.project_id else ""
        return f"[{self.get_status_display()}] {self.id}{proj}"

    # =====================================================
    # 领域方法 — 统一状态转移入口
    # =====================================================
    def transition_to(
        self,
        new_status: str,
        *,
        reason: str = "",
        node_id: str = "",
        save: bool = True,
    ) -> None:
        """状态转移。所有状态变更必须走此方法，保证可审计。

        Args:
            new_status: 目标状态（STATUS_* 之一）
            reason:     变更原因（人读字符串）
            node_id:    关联节点（可选）
            save:       是否立即保存（默认 True；批量操作时可 False）
        """
        from django.utils import timezone

        now = timezone.now()

        # 时间戳同步
        if new_status in (self.STATUS_RUNNING,) and self.started_at is None:
            self.started_at = now

        if new_status in (self.STATUS_DONE, self.STATUS_FAILED,
                          self.STATUS_CANCELLED):
            if self.finished_at is None:
                self.finished_at = now
            if self.started_at:
                delta = (now - self.started_at).total_seconds() * 1000
                self.total_duration_ms = max(self.total_duration_ms, int(delta))

        # 记录失败原因（仅在 failed 时）
        if new_status == self.STATUS_FAILED and reason:
            self.failure_reason = reason[:4096]
            if node_id:
                self.failure_node_id = node_id

        if node_id and new_status == self.STATUS_RUNNING:
            self.current_node_id = node_id

        self.status = new_status
        self.last_heartbeat_at = now

        if save:
            self.save(
                update_fields=[
                    "status", "current_node_id", "started_at",
                    "finished_at", "last_heartbeat_at", "total_duration_ms",
                    "failure_reason", "failure_node_id", "updated_at",
                ],
            )

    def pause(self, reason: str = "") -> None:
        self.transition_to(self.STATUS_PAUSED, reason=reason)

    def cancel(self, reason: str = "") -> None:
        self.transition_to(self.STATUS_CANCELLED, reason=reason)

    # =====================================================
    # 便捷查询
    # =====================================================
    @property
    def is_terminal(self) -> bool:
        """是否为已终结状态（done/failed/cancelled）"""
        return self.status in (self.STATUS_DONE,
                               self.STATUS_FAILED,
                               self.STATUS_CANCELLED)

    @property
    def is_active(self) -> bool:
        return self.status in (self.STATUS_RUNNING,
                               self.STATUS_PAUSED,
                               self.STATUS_WAITING_HUMAN)


# =========================================================
# NodeExecution — 节点级执行记录
# =========================================================
class NodeExecution(models.Model):
    """WorklowInstance 下的一次节点执行（含重试）。

    与现有 AgentExecutionRun 的关系：
      NodeExecution（1） ──▶ AgentExecutionRun（N）
      即：一个节点执行 = 一次高维调度，内部可能包含多次实际的 LLM 调用。
    """

    STATUS_PENDING   = "pending"
    STATUS_SKIPPED   = "skipped"
    STATUS_RUNNING   = "running"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED    = "failed"
    STATUS_TIMED_OUT = "timed_out"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING,   "待执行"),
        (STATUS_SKIPPED,   "条件跳过"),
        (STATUS_RUNNING,   "运行中"),
        (STATUS_SUCCEEDED, "成功"),
        (STATUS_FAILED,    "失败"),
        (STATUS_TIMED_OUT, "超时"),
        (STATUS_CANCELLED, "已取消"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name="node_executions",
        verbose_name="所属实例",
    )

    node_id = models.CharField("节点ID", max_length=64, db_index=True)
    node_name = models.CharField("节点名称", max_length=128, blank=True, default="")
    runner_type = models.CharField("节点类型", max_length=32, blank=True, default="")

    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES,
        default=STATUS_PENDING, db_index=True,
    )

    # ── 输入/输出快照 ───────────────────────────
    input_context  = models.JSONField("入参上下文", default=dict, blank=True)
    output_context = models.JSONField("出参上下文", default=dict, blank=True)
    errors         = models.JSONField("错误详情", default=list, blank=True)

    # ── 重试与计费 ─────────────────────────────
    attempt       = models.PositiveSmallIntegerField("第几次尝试", default=1)
    max_retries   = models.PositiveSmallIntegerField("最大重试次数", default=3)
    coin_cost     = models.PositiveIntegerField("消耗金币", default=0)
    llm_token_in  = models.PositiveIntegerField("输入Token", default=0)
    llm_token_out = models.PositiveIntegerField("输出Token", default=0)

    # ── 时间 ───────────────────────────────────
    started_at   = models.DateTimeField(null=True, blank=True)
    finished_at  = models.DateTimeField(null=True, blank=True)
    duration_ms  = models.PositiveIntegerField("耗时(ms)", default=0)

    # ── 关联现有执行记录（平滑迁移）───────────
    agent_execution_run_ids = models.JSONField(
        "关联 Agent 执行记录 ID", default=list, blank=True,
        help_text="与现有 AgentExecutionRun 关联的 ID 列表，便于从旧系统查询",
    )

    # ── 幂等键（用于防重复调度）───────────────
    idempotency_key = models.CharField(
        "幂等键", max_length=128, blank=True, default="",
        unique=True, db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workflow_node_execution"
        verbose_name = "工作流节点执行记录"
        verbose_name_plural = verbose_name
        ordering = ["instance_id", "created_at"]
        indexes = [
            models.Index(fields=["instance_id", "node_id", "status"],
                         name="ne_inst_node_status_idx"),
            models.Index(fields=["status", "-created_at"],
                         name="ne_status_created_idx"),
            models.Index(fields=["instance_id", "attempt"],
                         name="ne_inst_attempt_idx"),
        ]

    def __str__(self) -> str:
        return f"[{self.get_status_display()}] {self.node_id} " \
               f"(attempt={self.attempt}, inst={self.instance_id[:8]})"

    # =====================================================
    # 领域方法
    # =====================================================
    def mark_running(self, *, input_context: Optional[Dict] = None) -> None:
        from django.utils import timezone
        self.status = self.STATUS_RUNNING
        if input_context is not None:
            self.input_context = input_context
        self.started_at = timezone.now()
        self.save(update_fields=["status", "input_context",
                                 "started_at", "updated_at"])

    def mark_success(
        self,
        *,
        output_context: Optional[Dict] = None,
        coin_cost: int = 0,
        llm_token_in: int = 0,
        llm_token_out: int = 0,
    ) -> None:
        from django.utils import timezone
        self.status = self.STATUS_SUCCEEDED
        if output_context is not None:
            self.output_context = output_context
        self.coin_cost     = coin_cost
        self.llm_token_in  = llm_token_in
        self.llm_token_out = llm_token_out
        self.finished_at   = timezone.now()
        if self.started_at:
            self.duration_ms = int(
                (self.finished_at - self.started_at).total_seconds() * 1000,
            )
        self.save(update_fields=[
            "status", "output_context", "finished_at", "duration_ms",
            "coin_cost", "llm_token_in", "llm_token_out", "updated_at",
        ])

    def mark_failed(
        self,
        *,
        error: str,
        error_code: str = "unknown",
        coin_cost: int = 0,
    ) -> None:
        from django.utils import timezone
        self.status = self.STATUS_FAILED
        errors = list(self.errors or [])
        errors.append({"code": error_code, "message": error[:2000]})
        self.errors = errors
        self.coin_cost = coin_cost
        self.finished_at = timezone.now()
        if self.started_at:
            self.duration_ms = int(
                (self.finished_at - self.started_at).total_seconds() * 1000,
            )
        self.save(update_fields=[
            "status", "errors", "coin_cost",
            "finished_at", "duration_ms", "updated_at",
        ])

    def mark_skipped(self, *, reason: str = "condition_false") -> None:
        from django.utils import timezone
        self.status = self.STATUS_SKIPPED
        errors = list(self.errors or [])
        errors.append({"code": "skipped", "message": reason})
        self.errors = errors
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "errors",
                                 "finished_at", "updated_at"])


# =========================================================
# NodeExecutionLog — 节点内的事件/子调用追踪（轻量）
# =========================================================
class NodeExecutionEvent(models.Model):
    """NodeExecution 的细粒度事件，用于诊断/调试。

    通常 1 个 NodeExecution 内会有：
      - 1 次 agent_run 调用
      - N 次技能调用（通过现有 AgentExecutionRun 记录）
      - 1 次结果写回
    这里只记录关键事件时间点 + 简短说明，不走外键保证性能。
    """

    LEVEL_INFO = "info"
    LEVEL_WARN = "warn"
    LEVEL_ERROR = "error"
    LEVEL_CHOICES = [
        (LEVEL_INFO, "信息"),
        (LEVEL_WARN, "告警"),
        (LEVEL_ERROR, "错误"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(
        NodeExecution,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField("事件类型", max_length=32, default="generic")
    level = models.CharField(
        "级别", max_length=8, choices=LEVEL_CHOICES, default=LEVEL_INFO,
        db_index=True,
    )
    message = models.TextField("事件描述", blank=True, default="")
    duration_ms = models.PositiveIntegerField("耗时(ms)", default=0)
    extra = models.JSONField("附加数据", default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "workflow_node_execution_event"
        verbose_name = "节点执行事件"
        verbose_name_plural = verbose_name
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"[{self.get_level_display()}] {self.event_type} · {self.message[:40]}"


__all__: List[str] = [
    "WorkflowInstance",
    "NodeExecution",
    "NodeExecutionEvent",
]
