# -*- coding: utf-8 -*-
"""工作流包管理端 API（发布/校验/灰度/版本对比）
========================================================
本模块提供面向管理员的 API 层，包括：

  1. PackValidator：发布前的语法/结构/依赖校验
  2. PackPublisher：版本发布/灰度/回滚
  3. PackCompareRenderer：两个 pack 间版本对比输出

可直接在 Django View 或 DRF ViewSet 中使用：

    from apps.workflow.workflow_admin_api import PackPublisher, PackValidator

    # 发布前校验
    issues = PackValidator(pack).validate()

    # 发布
    PackPublisher(pack).publish(gray_weight=100, published_by="admin")

    # 回滚
    PackPublisher(pack).rollback_to(target_pack)

    # 生成 JSON 版本对比报告（前端可渲染 diff 树）
    diff = PackCompareRenderer(pack_a, pack_b).render_diff()

========================================================
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

from apps.workflow.condition_evaluator import safe_eval
from apps.workflow.execution_models import NodeExecution, WorkflowInstance
from apps.workflow.models import FusionPipelineNode, FusionPipelinePack


logger = logging.getLogger(__name__)


# =========================================================
# Issue 模型：校验结果的统一结构
# =========================================================
@dataclass_fallback
class PackIssue:
    """一条校验问题，level in {info, warning, error}。"""
    level: str
    code: str
    message: str
    node_id: str = ""
    detail: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "node_id": self.node_id,
            "detail": self.detail or {},
        }


# Python dataclass 在部分环境中需要保护：
def dataclass_fallback(cls):  # type: ignore
    """为普通类添加一个轻量级的 __init__ 构造（兼容低版本 Python）。"""
    try:
        from dataclasses import dataclass as _dc
        return _dc(cls)
    except Exception:
        def __init__(self, **kwargs):  # type: ignore
            for k, v in kwargs.items():
                setattr(self, k, v)
        cls.__init__ = __init__
        return cls


# =========================================================
# PackValidator：发布前校验
# =========================================================
class PackValidator:
    """对一个 FusionPipelinePack 进行全面校验。

    校验规则：
      1. 至少有一个节点，且 node 都 enabled
      2. upstream_deps 引用的节点必须存在
      3. DAG 不能有环（拓扑排序验证）
      4. condition_expr 如果非空必须能被安全表达式解析
      5. runtime_config.timeout_seconds 必须为正整数且 <= 3600
      6. 若配置了 extra_config（PARALLEL/ITERATE/HUMAN），
         结构必须合法
    """

    def __init__(self, pack: FusionPipelinePack):
        self.pack = pack
        self.nodes = list(pack.nodes.all())
        self.node_by_id = {n.fusion_node_id: n for n in self.nodes}

    # ---- 主入口 ----
    def validate(self) -> List[PackIssue]:
        issues: List[PackIssue] = []
        issues += self._validate_basics()
        issues += self._validate_dependencies()
        issues += self._validate_conditions()
        issues += self._validate_runtime_configs()
        issues += self._validate_extra_configs()
        issues += self._validate_no_cycle()
        return sorted(issues, key=lambda i: {"error": 0, "warning": 1, "info": 2}[i.level])

    # ---- 分组校验 ----
    def _validate_basics(self) -> List[PackIssue]:
        issues: List[PackIssue] = []
        if not self.nodes:
            issues.append(PackIssue("error", "EMPTY_PACK", "工作流包中没有节点定义"))
            return issues
        enabled = sum(1 for n in self.nodes if getattr(n, "enabled", True))
        if enabled == 0:
            issues.append(PackIssue("error", "ALL_NODES_DISABLED", "所有节点都被禁用"))
        return issues

    def _validate_dependencies(self) -> List[PackIssue]:
        issues: List[PackIssue] = []
        for n in self.nodes:
            for dep_id in (n.upstream_deps or []):
                if dep_id not in self.node_by_id:
                    issues.append(PackIssue(
                        "error", "UNKNOWN_DEP",
                        f"节点 {n.fusion_node_id} 的上游依赖 {dep_id} 不存在",
                        node_id=n.fusion_node_id,
                    ))
        return issues

    def _validate_conditions(self) -> List[PackIssue]:
        issues: List[PackIssue] = []
        for n in self.nodes:
            expr = getattr(n, "condition_expr", "") or ""
            if not expr.strip():
                continue
            try:
                safe_eval(expr, ctx={"test": 1}, constants={})
            except Exception as exc:  # noqa: BLE001
                issues.append(PackIssue(
                    "warning", "BAD_CONDITION_EXPR",
                    f"节点 {n.fusion_node_id} 的条件表达式无法求值: {exc}",
                    node_id=n.fusion_node_id,
                    detail={"expr": expr},
                ))
        return issues

    def _validate_runtime_configs(self) -> List[PackIssue]:
        issues: List[PackIssue] = []
        for n in self.nodes:
            cfg = getattr(n, "runtime_config", None) or {}
            timeout = cfg.get("timeout_seconds", 600)
            if not isinstance(timeout, int) or timeout <= 0 or timeout > 3600:
                issues.append(PackIssue(
                    "warning", "BAD_TIMEOUT",
                    f"节点 {n.fusion_node_id} 的 timeout_seconds = {timeout} "
                    f"应在 (0, 3600]",
                    node_id=n.fusion_node_id,
                ))
            retry = cfg.get("retry_policy", {}) or {}
            max_retries = retry.get("max_retries", 3)
            if not isinstance(max_retries, int) or max_retries < 0 or max_retries > 10:
                issues.append(PackIssue(
                    "warning", "BAD_RETRY_POLICY",
                    f"节点 {n.fusion_node_id} 的 max_retries = {max_retries} "
                    f"应在 [0, 10]",
                    node_id=n.fusion_node_id,
                ))
        return issues

    def _validate_extra_configs(self) -> List[PackIssue]:
        issues: List[PackIssue] = []
        for n in self.nodes:
            extra = getattr(n, "extra_config", None) or {}
            runner = getattr(n, "runner_type", "") or ""
            if runner == "parallel_group":
                if not isinstance(extra.get("parallel_group_key"), str):
                    issues.append(PackIssue(
                        "warning", "MISSING_PARALLEL_KEY",
                        f"并行节点 {n.fusion_node_id} 缺少 parallel_group_key 配置",
                        node_id=n.fusion_node_id,
                    ))
            elif runner == "iterate_loop":
                until = extra.get("iterate_until_condition") or {}
                if not (isinstance(until, dict) and until.get("field") and
                        until.get("operator") and "value" in until):
                    issues.append(PackIssue(
                        "warning", "MISSING_ITERATE_CONDITION",
                        f"循环节点 {n.fusion_node_id} 缺少 iterate_until_condition",
                        node_id=n.fusion_node_id,
                    ))
                if not isinstance(extra.get("iterate_max_attempts"), int) or extra.get("iterate_max_attempts") <= 0:
                    issues.append(PackIssue(
                        "warning", "BAD_ITERATE_MAX",
                        f"循环节点 {n.fusion_node_id} 的 iterate_max_attempts 应为正整数",
                        node_id=n.fusion_node_id,
                    ))
            elif runner == "human_gate":
                if not extra.get("human_gate_message"):
                    issues.append(PackIssue(
                        "info", "EMPTY_HUMAN_GATE_MSG",
                        f"人工门控节点 {n.fusion_node_id} 没有配置 human_gate_message",
                        node_id=n.fusion_node_id,
                    ))
        return issues

    def _validate_no_cycle(self) -> List[PackIssue]:
        """拓扑排序验证 DAG 无环。"""
        if not self.nodes:
            return []
        in_degree = {n.fusion_node_id: 0 for n in self.nodes}
        adj = {n.fusion_node_id: [] for n in self.nodes}
        for n in self.nodes:
            for dep_id in (n.upstream_deps or []):
                if dep_id in in_degree:
                    in_degree[n.fusion_node_id] += 1
                    adj[dep_id].append(n.fusion_node_id)

        queue = [nid for nid, d in in_degree.items() if d == 0]
        visited = 0
        while queue:
            current = queue.pop(0)
            visited += 1
            for nxt in adj[current]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)
        if visited != len(self.nodes):
            cyclic = [nid for nid, d in in_degree.items() if d > 0]
            return [PackIssue(
                "error", "CYCLIC_DAG",
                f"检测到依赖环：{', '.join(cyclic)}。请修改 upstream_deps",
            )]
        return []


# =========================================================
# PackPublisher：版本发布/灰度/回滚
# =========================================================
class PackPublisher:
    """工作流包的版本管理。"""

    def __init__(self, pack: FusionPipelinePack):
        self.pack = pack

    # ---- 发布 ----
    def publish(
        self,
        *,
        gray_weight: int = 100,
        published_by: str = "system",
        with_validation: bool = True,
    ) -> Tuple[bool, List[PackIssue], str]:
        """发布当前 pack：
        - gray_weight=100 → 全量发布（pack_status="active"）
        - 0 < gray_weight < 100 → 灰度发布（pack_status="gray"）
        - 校验失败 → 拒绝发布并返回 issues

        返回 (ok, issues, message)
        """
        if with_validation:
            issues = PackValidator(self.pack).validate()
            if any(i.level == "error" for i in issues):
                return False, issues, "存在错误级校验问题，发布被拒绝"
        else:
            issues = []

        # 以事务方式更新 pack 状态
        with transaction.atomic():
            self.pack.pack_status = (
                "active" if gray_weight >= 100 else "gray"
            )
            self.pack.gray_weight = int(max(0, min(100, gray_weight)))
            self.pack.published_by = published_by
            self.pack.published_at = timezone.now()
            # 灰度分流的配置开关：新引擎启用
            engine_cfg = dict(self.pack.engine_config or {})
            engine_cfg["enabled"] = True
            self.pack.engine_config = engine_cfg
            self.pack.save()

        logger.info("[PackPublisher] pack=%s version=%s 已发布 (gray=%s%% by=%s)",
                    self.pack.id, self.pack.version, gray_weight, published_by)
        return True, issues, "发布成功"

    # ---- 暂停灰度（恢复到草稿态，方便再次调整）----
    def pause(self, *, by: str = "admin") -> None:
        self.pack.pack_status = "draft"
        self.pack.gray_weight = 0
        self.pack.published_by = f"{by}(paused)"
        self.pack.save()

    # ---- 回滚 ----
    def rollback_to(self, target_pack: FusionPipelinePack, *, by: str = "admin") -> None:
        """将 target_pack 标记为当前默认 pack。

        用法：
          publisher = PackPublisher(current_pack)
          target = FusionPipelinePack.objects.get(version="旧版本号")
          publisher.rollback_to(target)
        """
        with transaction.atomic():
            # 先置空所有 is_default_for_creation = True 的 pack
            FusionPipelinePack.objects.filter(
                is_default_for_creation=True
            ).update(is_default_for_creation=False)
            target_pack.is_default_for_creation = True
            target_pack.pack_status = "active"
            target_pack.gray_weight = 100
            target_pack.published_by = f"{by}(rollback)"
            target_pack.published_at = timezone.now()
            target_pack.save()
            logger.info("[PackPublisher] 已回滚到 pack=%s version=%s (by=%s)",
                        target_pack.id, target_pack.version, by)


# =========================================================
# PackCompareRenderer：两版本差异（可前端渲染）
# =========================================================
class PackCompareRenderer:
    """为两个 pack 生成结构化的差异报告。"""

    def __init__(self, pack_a: FusionPipelinePack, pack_b: FusionPipelinePack):
        self.pack_a = pack_a
        self.pack_b = pack_b

    def render_diff(self) -> Dict[str, Any]:
        nodes_a = {n.fusion_node_id: n for n in self.pack_a.nodes.all()}
        nodes_b = {n.fusion_node_id: n for n in self.pack_b.nodes.all()}
        added = sorted(set(nodes_b) - set(nodes_a))
        removed = sorted(set(nodes_a) - set(nodes_b))
        shared = sorted(set(nodes_a) & set(nodes_b))
        changed = []
        for nid in shared:
            a = nodes_a[nid]
            b = nodes_b[nid]
            # 简单对比一些关键字段
            diff_fields = {}
            for field in ("runner_type", "chain_order", "condition_expr",
                          "runtime_config", "extra_config", "upstream_deps",
                          "coin_cost", "enabled"):
                va = getattr(a, field, None)
                vb = getattr(b, field, None)
                if va != vb:
                    diff_fields[field] = {"old": va, "new": vb}
            if diff_fields:
                changed.append({"node_id": nid, "fields": diff_fields})

        return {
            "pack_a": {"version": self.pack_a.version, "id": str(self.pack_a.id)},
            "pack_b": {"version": self.pack_b.version, "id": str(self.pack_b.id)},
            "added_nodes": added,
            "removed_nodes": removed,
            "changed_nodes": changed,
        }


__all__ = [
    "PackIssue",
    "PackValidator",
    "PackPublisher",
    "PackCompareRenderer",
]
