# -*- coding: utf-8 -*-
"""工作流调度器
========================================================
【P0】旧引擎全量下线 —— 本模块是创作流程的唯一调度入口。

职责：
  ① 创建 WorkflowInstance（唯一入口）
  ② 提交异步任务到 Celery（run_workflow_instance）
  ③ 外部控制（暂停/恢复/取消/重跑）
  ④ 灰度分流（gray_weight / gray_traffic_salt）

旧引擎（AgentOrchestrator / FusionOrchestrator）已全量下线，
所有创作请求必须走新引擎（WorkflowEngine）。

========================================================
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from django.db import transaction
from django.utils import timezone

from apps.workflow.execution_models import WorkflowInstance
from apps.workflow.models import FusionPipelinePack

if TYPE_CHECKING:
    from apps.creation.models import Project

logger = logging.getLogger(__name__)


# =========================================================
# 灰度：按 pack_id + user_id 稳定哈希
# =========================================================
def _gray_split(pack: FusionPipelinePack, user_id: str) -> bool:
    """基于灰度配置判断是否走新引擎。

    逻辑：hash(user_id + gray_traffic_salt) % 100 < gray_weight
    目的：稳定灰度（同一用户不会在同个 pack 上随机切换）
    """
    cfg = pack.engine_config or {}
    enabled = bool(cfg.get("enabled", False))
    if not enabled:
        return True  # 默认启用新引擎

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
        return True  # 出错默认启用


# =========================================================
# WorkflowScheduler
# =========================================================
class WorkflowScheduler:
    """创作流程的唯一调度入口（面向 Django/Python）。"""

    @classmethod
    def start_for_project(
        cls,
        project: "Project",
        *,
        user_id: str,
        pack_id: Optional[str] = None,
        start_node_id: Optional[str] = None,
    ) -> WorkflowInstance:
        """为某个创作项目启动工作流（唯一入口）。"""
        pack = cls._resolve_pack(pack_id)
        use_new = _gray_split(pack, user_id)

        logger.info(
            "[Scheduler] 启动创作 pack=%s project=%s user=%s new_engine=%s",
            pack.id, project.id, user_id, use_new,
        )

        # 始终创建 WorkflowInstance（新引擎）
        instance = WorkflowInstance.objects.create(
            pack=pack,
            project=project,
            user_id=user_id,
            trigger_type=WorkflowInstance.TRIGGER_USER,
            start_node_id=start_node_id or "",
        )

        # 提交到 Celery 异步执行
        try:
            from apps.workflow.tasks import run_workflow_instance
            run_workflow_instance.delay(str(instance.id), start_node_id=start_node_id)
        except Exception as exc:
            logger.error("[Scheduler] Celery 提交失败，降级同步执行: %s", exc)
            _run_instance_sync(str(instance.id), start_node_id)

        return instance

    @classmethod
    def resume(
        cls,
        instance_id: str,
        *,
        start_node_id: Optional[str] = None,
    ) -> None:
        """从断点恢复执行。"""
        try:
            from apps.workflow.tasks import run_workflow_instance
            run_workflow_instance.delay(instance_id, start_node_id=start_node_id)
        except Exception as exc:
            logger.error("[Scheduler] resume Celery 失败，降级同步: %s", exc)
            _run_instance_sync(instance_id, start_node_id)

    @classmethod
    def pause(cls, instance_id: str) -> None:
        """标记实例为 paused（引擎心跳识别后中断）。"""
        rows = WorkflowInstance.objects.filter(id=instance_id).update(
            status=WorkflowInstance.STATUS_PAUSED,
            updated_at=timezone.now(),
        )
        logger.info("[Scheduler] pause %s → %s rows", instance_id, rows)

    @classmethod
    def cancel(
        cls,
        instance_id: str,
        reason: str = "cancelled_by_user",
    ) -> None:
        with transaction.atomic():
            rows = WorkflowInstance.objects.select_for_update().filter(
                id=instance_id,
            ).update(
                status=WorkflowInstance.STATUS_CANCELLED,
                failure_reason=reason[:4096],
                finished_at=timezone.now(),
            )
            logger.info("[Scheduler] cancel %s → %s rows", instance_id, rows)

    # ── Pack 解析 ──────────────────────────────────────
    @classmethod
    def _resolve_pack(cls, pack_id: Optional[str]) -> FusionPipelinePack:
        if pack_id:
            try:
                return FusionPipelinePack.objects.get(id=pack_id)
            except FusionPipelinePack.DoesNotExist:
                logger.warning(
                    "[Scheduler] 指定 pack_id=%s 不存在，尝试默认 pack", pack_id,
                )
        # 优先取 is_active=True 的包
        active = FusionPipelinePack.objects.filter(is_active=True).order_by(
            "-updated_at"
        ).first()
        if active:
            return active
        # 回退：取最新的任意包
        fallback = FusionPipelinePack.objects.order_by("-updated_at").first()
        if fallback:
            return fallback
        raise RuntimeError(
            "[Scheduler] 系统中没有任何 FusionPipelinePack，请先创建工作流包",
        )


# =========================================================
# 同步执行（Celery 不可用时的降级路径）
# =========================================================
def _run_instance_sync(instance_id: str, start_node_id: Optional[str]) -> None:
    try:
        from apps.workflow.workflow_engine import WorkflowEngine

        instance = WorkflowInstance.objects.get(id=instance_id)
        engine = WorkflowEngine(instance)
        engine.run(start_node_id=start_node_id)
    except Exception as exc:
        logger.exception("[run_instance_sync] 同步执行崩溃: %s", exc)
        WorkflowInstance.objects.filter(id=instance_id).update(
            status=WorkflowInstance.STATUS_FAILED,
            failure_reason=f"run_sync_fatal:{type(exc).__name__}:{exc}",
            finished_at=timezone.now(),
        )


__all__ = [
    "WorkflowScheduler",
    "_run_instance_sync",
    "_gray_split",
]
