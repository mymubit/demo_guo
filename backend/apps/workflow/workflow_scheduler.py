# -*- coding: utf-8 -*-
"""工作流调度器 + Celery 任务入口
========================================================
WorkflowScheduler 负责：
  ① 创建 WorkflowInstance（用户点击"开始创作"时调用）
  ② 提交异步任务到 Celery（run_workflow_instance.delay）
  ③ 外部控制（暂停/恢复/取消/重跑某个节点）
  ④ 灰度分流（gray_weight / gray_traffic_salt）

run_workflow_instance：Celery 任务函数，负责：
  - 加载 WorkflowInstance
  - 实例化 WorkflowEngine
  - 执行完整工作流
  - 错误兜底（崩溃时写回 failed 状态）
========================================================
"""
from __future__ import annotations

import logging
from typing import Optional

from django.utils import timezone

from apps.workflow.execution_models import NodeExecution, WorkflowInstance
from apps.workflow.models import FusionPipelinePack

logger = logging.getLogger(__name__)


# =========================================================
# 灰度：按 pack_id + user_id 稳定哈希分流
# =========================================================
def _is_new_engine_for(pack: FusionPipelinePack, user_id: str) -> bool:
    """基于灰度配置判断是否走新引擎。

    逻辑：hash(user_id + gray_traffic_salt) % 100 < gray_weight
    目的：稳定灰度（同一用户不会在同个 pack 上随机切换）
    """
    cfg = pack.engine_config or {}
    enabled = bool(cfg.get("enabled", False))
    if not enabled:
        return False

    weight = int(cfg.get("gray_weight", 0) or pack.gray_weight or 0)
    if weight >= 100:
        return True
    if weight <= 0:
        return False

    salt = cfg.get("gray_traffic_salt") or pack.gray_traffic_salt or str(pack.id)
    try:
        h = 0
        for ch in f"{user_id}:{salt}":
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return (h % 100) < weight
    except Exception:
        return False


# =========================================================
# Scheduler：外部事件入口
# =========================================================
class WorkflowScheduler:
    """外部系统调用工作流的统一入口（面向 Django/Python）。"""

    @classmethod
    def start_for_project(
        cls,
        project: "Any",  # creation.Project
        *,
        user_id: str,
        pack_id: Optional[str] = None,
        start_node_id: Optional[str] = None,
        force_new_engine: Optional[bool] = None,
    ) -> WorkflowInstance:
        """为某个创作项目启动工作流。

        双轨策略：
          • force_new_engine=True  → 强制走新引擎
          • force_new_engine=False → 强制走旧引擎（AgentOrchestrator）
          • None                    → 按灰度配置自动选择
        """
        pack = cls._resolve_pack(pack_id)
        use_new_engine = (
            force_new_engine
            if force_new_engine is not None
            else _is_new_engine_for(pack, user_id)
        )

        logger.info(
            "[Scheduler] pack=%s project=%s user=%s use_new_engine=%s",
            pack.id, project.id, user_id, use_new_engine,
        )

        if not use_new_engine:
            # 走旧引擎（创建空实例记录用于追踪，不写入执行数据）
            instance = WorkflowInstance.objects.create(
                pack=pack,
                project=project,
                user_id=user_id,
                trigger_type="user",
                status="running",
                started_at=timezone.now(),
                context={"legacy_engine": True},
            )
            # 旧引擎由 creation.views 调用，这里只返回占位实例
            # 旧引擎执行完成后应调用 WorkflowScheduler.mark_legacy_done()
            return instance

        # 新引擎：创建实例 + 异步调度
        instance = WorkflowInstance.objects.create(
            pack=pack,
            project=project,
            user_id=user_id,
            trigger_type="user",
            start_node_id=start_node_id or "",
        )

        # 提交到 Celery（try-catch：若 Celery 不可用，降级为同步执行）
        try:
            from apps.workflow.tasks import run_workflow_instance
            run_workflow_instance.delay(str(instance.id), start_node_id=start_node_id)
        except Exception as exc:
            logger.error(
                "[Scheduler] Celery 提交失败，降级同步执行: %s", exc,
            )
            _run_instance_sync(instance.id, start_node_id)

        return instance

    @classmethod
    def resume(cls, instance_id: str, *, start_node_id: Optional[str] = None) -> None:
        """从断点恢复执行。"""
        try:
            from apps.workflow.tasks import run_workflow_instance
            run_workflow_instance.delay(instance_id, start_node_id=start_node_id)
        except Exception as exc:
            logger.error("[Scheduler] resume Celery 失败，降级同步: %s", exc)
            _run_instance_sync(instance_id, start_node_id)

    @classmethod
    def pause(cls, instance_id: str) -> None:
        """标记实例为 paused（由引擎内部下一次心跳时识别中断）。"""
        rows = WorkflowInstance.objects.filter(id=instance_id).update(
            status="paused",
            updated_at=timezone.now(),
        )
        logger.info("[Scheduler] pause %s → %s rows", instance_id, rows)

    @classmethod
    def cancel(cls, instance_id: str, reason: str = "cancelled_by_user") -> None:
        WorkflowInstance.objects.filter(id=instance_id).update(
            status="cancelled",
            failure_reason=reason,
            finished_at=timezone.now(),
        )

    @classmethod
    def mark_legacy_done(
        cls,
        instance_id: str,
        *,
        success: bool,
        summary: str = "",
    ) -> None:
        """旧引擎执行完成后调用此方法收尾，保证统计闭环。"""
        updates = {
            "status": "done" if success else "failed",
            "finished_at": timezone.now(),
            "updated_at": timezone.now(),
        }
        if not success:
            updates["failure_reason"] = summary[:2000]
        WorkflowInstance.objects.filter(id=instance_id).update(**updates)

    # ── 私有：pack 解析 ──
    @classmethod
    def _resolve_pack(cls, pack_id: Optional[str]) -> "FusionPipelinePack":
        if pack_id:
            try:
                return FusionPipelinePack.objects.get(id=pack_id)
            except FusionPipelinePack.DoesNotExist:
                logger.warning("[Scheduler] 指定 pack_id=%s 不存在，回退默认", pack_id)
        # 取当前启用的 pack（is_active=True 的默认工作流包）
        return (
            FusionPipelinePack.objects.filter(is_active=True)
            .order_by("-updated_at")
            .first()
            or FusionPipelinePack.objects.order_by("-updated_at").first()
        )


# =========================================================
# 同步执行（当 Celery 不可用时的降级路径）
# =========================================================
def _run_instance_sync(instance_id: str, start_node_id: Optional[str]) -> None:
    try:
        from apps.workflow.workflow_engine import WorkflowEngine
        instance = WorkflowInstance.objects.get(id=instance_id)
        engine = WorkflowEngine(instance)
        engine.run(start_node_id=start_node_id)
    except Exception as exc:
        logger.exception("[run_instance_sync] 同步执行崩溃: %s", exc)
        # 最后一道防线：写回失败状态
        WorkflowInstance.objects.filter(id=instance_id).update(
            status="failed",
            failure_reason=f"run_sync_fatal:{type(exc).__name__}:{exc}",
            finished_at=timezone.now(),
        )


__all__ = [
    "WorkflowScheduler",
    "_run_instance_sync",
]
