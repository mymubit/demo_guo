# -*- coding: utf-8 -*-
"""编排引擎调试与上下文压缩
========================================================
WorkflowDebugRunner：为管理端提供"干跑"能力，用于：
  - 不真正调用 LLM 的情况下验证工作流结构
  - 展示执行计划（会走哪些节点 / 按什么顺序）
  - 预测每个节点需要的金币数量
  - 检测条件表达式在"虚拟"输入下的真假

ContextCompressor：
  - 对 WorkflowInstance.context 进行体积控制
  - 默认使用 JSON round-trip 过滤 + TTL 压缩
  - 在体积超过阈值时降级为仅保留"关键字段"

使用示例：
    from apps.workflow.workflow_debug_runner import (
        WorkflowDebugRunner, ContextCompressor,
    )

    debug = WorkflowDebugRunner(pack, mock_context={"topic": "爱情剧"})
    report = debug.run()
    # report = {
    #   "exec_plan": [...],
    #   "would_fail_at": [],
    #   "estimated_coin_total": 320,
    #   "estimated_seconds": 210,
    #   "condition_traces": [...],
    # }

    # 压缩一个大体积的上下文
    compressed = ContextCompressor().compress(instance.context)
========================================================
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from apps.workflow.condition_evaluator import safe_eval

logger = logging.getLogger(__name__)


# =========================================================
# WorkflowDebugRunner：预览/调试/成本估算
# =========================================================
class WorkflowDebugRunner:
    """以 dry_run 方式模拟执行一个工作流。

    关键特性：
      - 只读 pack，不写 DB
      - 不调用实际的 LLM 接口
      - 产出"如果真实执行"时的预期节点序列、耗时估算、金币估算、条件分支
    """

    # 粗略的节点类型系数（用于估算耗时/金币）
    _RUNNER_PROFILE = {
        "fusion_node":   {"seconds": 30,  "coin": 30},
        "fusion_review": {"seconds": 20,  "coin": 15},
        "fusion_score":  {"seconds": 10,  "coin": 5},
        "agent_chain":   {"seconds": 15,  "coin": 10},
        "parallel_group": {"seconds": 25, "coin": 20},  # 串行模拟
        "iterate_loop": {"seconds": 30, "coin": 25},
        "human_gate":   {"seconds": 60,  "coin": 0},
        "":              {"seconds": 25,  "coin": 20},  # 兜底
    }

    def __init__(
        self,
        pack: FusionPipelinePack,
        *,
        mock_context: Optional[Dict[str, Any]] = None,
        start_node_id: Optional[str] = None,
    ) -> None:
        self.pack = pack
        self.nodes = list(pack.nodes.all().order_by("chain_order"))
        self.node_by_id = {n.fusion_node_id: n for n in self.nodes}
        self.context = mock_context or {}
        self.start_node_id = start_node_id

    # ---- 执行计划（按依赖排序） ----
    def build_execution_plan(self) -> List[Dict[str, Any]]:
        """返回预计会执行的节点列表（包含条件判断结果）。"""
        if any(n.upstream_deps for n in self.nodes if n.upstream_deps):
            # 拓扑序
            return self._topological_plan()
        # 线性（chain_order）
        return [self._node_to_plan(n, idx) for idx, n in enumerate(self.nodes)]

    def _topological_plan(self) -> List[Dict[str, Any]]:
        in_degree = {n.fusion_node_id: 0 for n in self.nodes}
        adj: Dict[str, List[str]] = {n.fusion_node_id: [] for n in self.nodes}
        for n in self.nodes:
            for dep in (n.upstream_deps or []):
                if dep in in_degree:
                    in_degree[n.fusion_node_id] += 1
                    adj[dep].append(n.fusion_node_id)

        queue = sorted(
            [nid for nid, d in in_degree.items() if d == 0],
            key=lambda x: self.node_by_id[x].chain_order,
        )
        plan = []
        idx = 0
        while queue:
            current = queue.pop(0)
            plan.append(self._node_to_plan(self.node_by_id[current], idx))
            idx += 1
            for nxt in adj[current]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)
            queue.sort(key=lambda x: self.node_by_id[x].chain_order)
        if len(plan) != len(self.nodes):
            missing = set(self.node_by_id) - {p["node_id"] for p in plan}
            plan.append({
                "order": idx,
                "node_id": "⚠ 循环依赖节点（已忽略）",
                "runner_type": "error",
                "node_name": ", ".join(sorted(missing)),
                "reason": "CYCLE_DETECTED",
            })
        return plan

    def _node_to_plan(self, node: FusionPipelineNode, idx: int) -> Dict[str, Any]:
        cond_expr = getattr(node, "condition_expr", "") or ""
        cond_hit = None
        if cond_expr:
            try:
                cond_hit = bool(safe_eval(
                    cond_expr,
                    ctx=self.context,
                    constants={},
                ))
            except Exception:
                cond_hit = None

        profile = self._RUNNER_PROFILE.get(
            node.runner_type or "", self._RUNNER_PROFILE[""]
        )
        retry_policy = ((node.runtime_config or {}).get("retry_policy") or {})
        max_retries = int(retry_policy.get("max_retries", 0) or 0)

        return {
            "order": idx,
            "node_id": node.fusion_node_id,
            "node_name": node.name,
            "runner_type": node.runner_type or "",
            "condition_expr": cond_expr,
            "condition_would_hit": cond_hit,  # True/False/None(表达式错误)
            "estimated_seconds": profile["seconds"] * (1 + max_retries // 2),
            "estimated_coin": int(
                (node.coin_cost or profile["coin"]) * (1 + max_retries // 2)
            ),
            "upstream_deps": list(getattr(node, "upstream_deps", None) or []),
            "runtime_config": node.runtime_config or {},
        }

    # ---- 主入口：生成完整报告 ----
    def run(self) -> Dict[str, Any]:
        plan = self.build_execution_plan()
        would_fail_at = [
            p for p in plan
            if p.get("condition_would_hit") is None and p.get("condition_expr")
        ]
        total_seconds = sum(p.get("estimated_seconds", 0) for p in plan if p.get("runner_type") != "error")
        total_coin = sum(p.get("estimated_coin", 0) for p in plan)

        return {
            "pack": {"version": self.pack.version, "id": str(self.pack.id)},
            "mock_context_keys": list(self.context.keys()),
            "start_node_id": self.start_node_id,
            "execution_plan": plan,
            "would_fail_at": would_fail_at,
            "estimated_total_seconds": total_seconds,
            "estimated_total_coin": total_coin,
            "cycle_free": all(p.get("runner_type") != "error" for p in plan),
        }


# =========================================================
# ContextCompressor：控制上下文体积
# =========================================================
class ContextCompressor:
    """简单但实用的上下文压缩器。

    策略：
      1. 若 JSON 大小 <= soft_limit_bytes：原样返回
      2. 否则：
         - 对 str 类型字段截断到 max_str_len
         - 对 list 截断到 max_list_len
         - 对 dict 保留前 max_dict_keys 个键值
         - 删除所有 None/空值
      3. 若仍超 hard_limit_bytes：只保留节点输出摘要（节点ID/金币/耗时）
    """

    DEFAULT_SOFT_LIMIT = 200 * 1024  # 200 KB
    DEFAULT_HARD_LIMIT = 512 * 1024  # 512 KB
    DEFAULT_MAX_STR_LEN = 500
    DEFAULT_MAX_LIST_LEN = 20
    DEFAULT_MAX_DICT_KEYS = 30

    def __init__(
        self,
        *,
        soft_limit_bytes: int = DEFAULT_SOFT_LIMIT,
        hard_limit_bytes: int = DEFAULT_HARD_LIMIT,
        max_str_len: int = DEFAULT_MAX_STR_LEN,
        max_list_len: int = DEFAULT_MAX_LIST_LEN,
        max_dict_keys: int = DEFAULT_MAX_DICT_KEYS,
    ) -> None:
        self.soft_limit = soft_limit_bytes
        self.hard_limit = hard_limit_bytes
        self.max_str_len = max_str_len
        self.max_list_len = max_list_len
        self.max_dict_keys = max_dict_keys

    def compress(self, context: Any) -> Tuple[Any, Dict[str, Any]]:
        """返回 (压缩后的上下文, 压缩统计)。"""
        if context is None or context == {}:
            return context, {"bytes_before": 0, "bytes_after": 0, "level": 0}

        try:
            raw = json.dumps(context, ensure_ascii=False, default=str)
        except TypeError:
            raw = str(context)

        bytes_before = len(raw.encode("utf-8"))
        if bytes_before <= self.soft_limit:
            return context, {
                "bytes_before": bytes_before,
                "bytes_after": bytes_before,
                "level": 0,  # 0 = 未压缩
            }

        # Level 1：字段截断
        lvl1 = self._truncate(context, level=1)
        bytes_lvl1 = len(json.dumps(lvl1, ensure_ascii=False, default=str).encode("utf-8"))
        if bytes_lvl1 <= self.hard_limit:
            return lvl1, {
                "bytes_before": bytes_before,
                "bytes_after": bytes_lvl1,
                "level": 1,
                "reduction_pct": round((1 - bytes_lvl1 / bytes_before) * 100, 1),
            }

        # Level 2：仅保留摘要（每个节点只存节点ID/耗时/金币/状态）
        lvl2 = self._summary(context)
        bytes_lvl2 = len(json.dumps(lvl2, ensure_ascii=False, default=str).encode("utf-8"))
        return lvl2, {
            "bytes_before": bytes_before,
            "bytes_after": bytes_lvl2,
            "level": 2,
            "reduction_pct": round((1 - bytes_lvl2 / bytes_before) * 100, 1),
        }

    def _truncate(self, value: Any, *, level: int) -> Any:
        if isinstance(value, str):
            if len(value) > self.max_str_len:
                return value[: self.max_str_len] + "...<truncated>"
            return value
        if isinstance(value, list):
            if len(value) > self.max_list_len:
                return [
                    self._truncate(v, level=level)
                    for v in value[: self.max_list_len]
                ] + [f"...<+{len(value) - self.max_list_len} items truncated>"]
            return [self._truncate(v, level=level) for v in value]
        if isinstance(value, tuple):
            return tuple(self._truncate(list(value), level=level))
        if isinstance(value, dict):
            items = list(value.items())
            if len(items) > self.max_dict_keys:
                # 保留常用字段：优先保留 "nodes" / "current_node_id" 等关键字
                priority_keys = {"nodes", "current_node_id", "pack_version",
                                 "started_at", "trigger_type"}
                kept = [(k, v) for k, v in items if k in priority_keys]
                remaining = [(k, v) for k, v in items if k not in priority_keys]
                items = kept + remaining[: self.max_dict_keys - len(kept)]
                return {
                    k: self._truncate(v, level=level) for k, v in items
                }
            return {k: self._truncate(v, level=level) for k, v in items}
        # 其它类型（int/bool/None）—— 直接返回
        return value

    def _summary(self, context: Any) -> Dict[str, Any]:
        """最高级降级 —— 只保留全局元信息。"""
        if not isinstance(context, dict):
            return {"summary": str(context)[:200]}
        summary: Dict[str, Any] = {
            "keys": list(context.keys()),
            "_compressed_level": 2,
        }
        # 如果有 "nodes" 子字典，只存每个节点的摘要
        nodes = context.get("nodes")
        if isinstance(nodes, dict):
            summary["nodes_summary"] = {
                k: self._leaf_summary(v) for k, v in nodes.items()
            }
        return summary

    @staticmethod
    def _leaf_summary(value: Any) -> Any:
        if isinstance(value, dict):
            # 只保留数值型字段、短字符串
            out: Dict[str, Any] = {}
            for k, v in value.items():
                if isinstance(v, (int, float, bool)):
                    out[k] = v
                elif isinstance(v, str) and len(v) <= 60:
                    out[k] = v
                elif isinstance(v, str):
                    out[k] = v[:60] + "...<truncated>"
            return out
        if isinstance(value, (list, tuple)):
            return {"len": len(value)}
        return {"type": type(value).__name__}


# =========================================================
# 便捷入口
# =========================================================
def debug_pack(pack: FusionPipelinePack, *, mock_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """一行代码：快速生成 pack 的"干跑"报告。"""
    return WorkflowDebugRunner(pack, mock_context=mock_context).run()


def compress_instance_context(
    instance,
    *,
    soft_limit_bytes: int = 200 * 1024,
    hard_limit_bytes: int = 512 * 1024,
) -> Dict[str, Any]:
    """对一个 WorkflowInstance 的 context 就地压缩并保存。"""
    compressor = ContextCompressor(
        soft_limit_bytes=soft_limit_bytes,
        hard_limit_bytes=hard_limit_bytes,
    )
    new_ctx, stats = compressor.compress(instance.context or {})
    if stats.get("level", 0) > 0:
        instance.context = new_ctx
        # 保存到 DB（不修改 updated_at，以免干扰监控）
        instance.save(update_fields=["context"])
        logger.info("[ContextCompressor] instance=%s: from %s bytes -> %s bytes (level=%s, %s%% reduction)",
                    instance.id, stats["bytes_before"], stats["bytes_after"],
                    stats["level"], stats.get("reduction_pct", 0))
    return stats


__all__ = [
    "WorkflowDebugRunner",
    "ContextCompressor",
    "debug_pack",
    "compress_instance_context",
]
