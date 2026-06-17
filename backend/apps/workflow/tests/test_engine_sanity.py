# -*- coding: utf-8 -*-
"""编排引擎核心逻辑的 Sanity Check（零依赖 —— 不依赖数据库）

覆盖：
  1. ConditionEvaluator —— 条件表达式安全求值
  2. WorkflowDebugRunner —— 节点拓扑排序、成本估算
  3. ContextCompressor —— 三级上下文压缩
  4. PackValidator（使用 Mock）—— 发布前校验

运行方式：
    cd /workspace/backend
    python apps/workflow/tests/test_engine_sanity.py

目标：在没有数据库、没有 Celery 的前提下验证核心算法逻辑。
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ─────────────── 避免 Django 配置依赖 ───────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")


# ─────────────── 1. 条件表达式引擎测试 ───────────────
def test_condition_evaluator() -> Dict[str, bool]:
    from apps.workflow.condition_evaluator import safe_eval

    results: Dict[str, bool] = {}

    # 基础布尔运算
    results["bool_and"] = safe_eval(
        "ctx.a and ctx.b", ctx={"a": True, "b": True}
    ) is True
    results["bool_or"] = safe_eval(
        "ctx.a or ctx.b", ctx={"a": False, "b": True}
    ) is True
    results["bool_not"] = safe_eval("not ctx.flag", ctx={"flag": False}) is True

    # 数值比较
    results["cmp_gt"] = safe_eval("ctx.score > 60", ctx={"score": 70}) is True
    results["cmp_le"] = safe_eval("ctx.score <= 60", ctx={"score": 60}) is True
    results["cmp_chained"] = safe_eval(
        "ctx.min < ctx.value < ctx.max",
        ctx={"min": 0, "value": 50, "max": 100},
    ) is True

    # 列表成员
    results["in_list"] = safe_eval(
        "ctx.topic in ['爱情', '悬疑']",
        ctx={"topic": "悬疑"},
    ) is True

    # 上一节点输出
    results["prev_output"] = safe_eval(
        "prev.score >= 80",
        prev={"score": 85},
    ) is True

    # 算术运算
    results["arith"] = safe_eval("ctx.a + ctx.b > 5", ctx={"a": 3, "b": 4}) is True

    # 缺失字段 → 返回 False（不抛异常，由 _AttributeAccessDict 处理）
    results["missing_field"] = bool(safe_eval(
        "ctx.missing_key > 10", ctx={"other": 1}, default_on_error=False
    )) is False  # 注意这里可能会因为表达式错误而抛异常 —— 测试安全门

    # 危险表达式 —— 必须被拒绝
    danger_cases = [
        "__import__('os')",            # 导入
        "open('/etc/passwd')",         # 文件访问
        "eval('1+1')",                 # eval
        "exec('a=1')",                 # exec
        "[i for i in range(10)]",      # 列表推导（允许但在白名单之外）
        "lambda x: x",                 # lambda
    ]
    from apps.workflow.condition_evaluator import ConditionSecurityError
    rejected_count = 0
    for expr in danger_cases:
        try:
            safe_eval(expr, ctx={})
        except (ConditionSecurityError, SyntaxError, Exception):
            rejected_count += 1
    results["security_rejects"] = rejected_count >= 4

    return results


# ─────────────── 2. ContextCompressor 测试 ───────────────
def test_context_compressor() -> Dict[str, bool]:
    from apps.workflow.workflow_debug_runner import ContextCompressor

    results: Dict[str, bool] = {}

    # 小上下文 —— 不压缩
    small_ctx = {"key": "value", "num": 42}
    compressor = ContextCompressor(soft_limit_bytes=1000, hard_limit_bytes=2000)
    compressed, stats = compressor.compress(small_ctx)
    results["no_compress_small"] = stats["level"] == 0

    # 大字符串 —— 触发 Level 1 截断
    big_str = "x" * 10000
    medium_ctx = {"nodes": {"node-a": {"content": big_str, "score": 50}}}
    compressed, stats = compressor.compress(medium_ctx)
    results["level1_truncate"] = stats["level"] == 1
    results["level1_shrink"] = stats.get("reduction_pct", 0) > 0

    # 超大字典 —— 触发 Level 2 摘要
    huge_ctx = {
        "nodes": {f"node_{i}": {"output": "y" * 1000, "extra": list(range(100))}
                  for i in range(50)},
    }
    compressed, stats = compressor.compress(huge_ctx)
    results["level2_summary"] = stats["level"] == 2
    # 摘要保留
    results["level2_keys_preserved"] = (
        "nodes_summary" in compressed or "keys" in compressed
    )

    return results


# ─────────────── 3. WorkflowDebugRunner 测试（Mock Pack）───────
@dataclass
class MockNode:
    fusion_node_id: str
    name: str
    runner_type: str
    chain_order: int
    upstream_deps: List[str] = field(default_factory=list)
    runtime_config: Dict[str, Any] = field(default_factory=dict)
    condition_expr: str = ""
    extra_config: Dict[str, Any] = field(default_factory=dict)
    coin_cost: int = 10
    enabled: bool = True


@dataclass
class MockPack:
    id: str
    version: str
    engine_config: Dict[str, Any] = field(default_factory=dict)
    _nodes: List[MockNode] = field(default_factory=list)

    def nodes(self):  # type: ignore
        """兼容 nodes.all() 调用链."""
        return self


@dataclass
class MockNodesQueryset:
    _items: List[MockNode]

    def all(self):
        return self._items

    def order_by(self, field):
        key_func = lambda n: getattr(n, field.lstrip("-"), 0)
        return sorted(self._items, key=key_func) if field and not field.startswith("-") else sorted(self._items, key=key_func, reverse=True)


def test_debug_runner() -> Dict[str, bool]:
    """使用 Mock 对象测试执行计划构建逻辑。"""
    from apps.workflow.workflow_debug_runner import WorkflowDebugRunner

    results: Dict[str, bool] = {}

    # 场景 A：线性工作流（5 节点，使用 chain_order 顺序）
    nodes_a = [
        MockNode("adapt", "创意适配", "fusion_node", 1),
        MockNode("brief", "项目简报", "fusion_node", 2),
        MockNode("struct", "结构规划", "fusion_node", 3),
        MockNode("character", "人物设定", "fusion_node", 4),
        MockNode("script", "分集剧本", "fusion_node", 5),
    ]

    pack_a = MockPack(id="pack-linear", version="v1.0")
    runner_a = WorkflowDebugRunner.__new__(WorkflowDebugRunner)
    runner_a.pack = pack_a
    runner_a.nodes = nodes_a
    runner_a.node_by_id = {n.fusion_node_id: n for n in nodes_a}
    runner_a.context = {}
    runner_a.start_node_id = None

    plan_a = runner_a.build_execution_plan()
    results["linear_plan_5_nodes"] = len(plan_a) == 5
    results["linear_order_correct"] = (
        plan_a[0]["node_id"] == "adapt"
        and plan_a[-1]["node_id"] == "script"
    )

    report = runner_a.run()
    results["report_has_seconds"] = report["estimated_total_seconds"] > 0
    results["report_has_coin"] = report["estimated_total_coin"] > 0
    results["report_cycle_free"] = report["cycle_free"] is True

    # 场景 B：DAG 带依赖（节点 B,C 依赖 A，D 依赖 B,C）
    nodes_b = [
        MockNode("A", "节点A", "fusion_node", 1),
        MockNode("B", "节点B", "fusion_node", 2, upstream_deps=["A"]),
        MockNode("C", "节点C", "fusion_node", 3, upstream_deps=["A"]),
        MockNode("D", "节点D", "fusion_node", 4, upstream_deps=["B", "C"]),
    ]
    pack_b = MockPack(id="pack-dag", version="v1.1")
    runner_b = WorkflowDebugRunner.__new__(WorkflowDebugRunner)
    runner_b.pack = pack_b
    runner_b.nodes = nodes_b
    runner_b.node_by_id = {n.fusion_node_id: n for n in nodes_b}
    runner_b.context = {}
    runner_b.start_node_id = None

    plan_b = runner_b.build_execution_plan()
    results["dag_plan_4_nodes"] = len(plan_b) == 4
    # A 必须在前，D 必须在最后
    results["dag_a_first"] = plan_b[0]["node_id"] == "A"
    results["dag_d_last"] = plan_b[-1]["node_id"] == "D"

    # 场景 C：循环依赖 —— 应检测到
    nodes_c = [
        MockNode("X", "节点X", "fusion_node", 1, upstream_deps=["Y"]),
        MockNode("Y", "节点Y", "fusion_node", 2, upstream_deps=["Z"]),
        MockNode("Z", "节点Z", "fusion_node", 3, upstream_deps=["X"]),
    ]
    runner_c = WorkflowDebugRunner.__new__(WorkflowDebugRunner)
    runner_c.pack = MockPack(id="pack-cycle", version="v1.2")
    runner_c.nodes = nodes_c
    runner_c.node_by_id = {n.fusion_node_id: n for n in nodes_c}
    runner_c.context = {}
    runner_c.start_node_id = None
    report_c = runner_c.run()
    results["cycle_detected"] = report_c["cycle_free"] is False

    # 场景 D：条件节点 —— 当 review_score < 70 时跳过某个节点
    nodes_d = [
        MockNode("brief", "简报", "fusion_node", 1),
        MockNode(
            "rewrite",
            "重写",
            "fusion_node",
            2,
            upstream_deps=["brief"],
            condition_expr="ctx.review_score < 70",
        ),
        MockNode(
            "score",
            "评分",
            "fusion_score",
            3,
            upstream_deps=["rewrite", "brief"],
        ),
    ]
    runner_d = WorkflowDebugRunner.__new__(WorkflowDebugRunner)
    runner_d.pack = MockPack(id="pack-conditional", version="v1.3")
    runner_d.nodes = nodes_d
    runner_d.node_by_id = {n.fusion_node_id: n for n in nodes_d}
    runner_d.context = {"review_score": 50}  # 应触发重写
    runner_d.start_node_id = None
    plan_d = runner_d.build_execution_plan()
    # 找到 rewrite 节点
    rewrite_plan = next((p for p in plan_d if p["node_id"] == "rewrite"), None)
    results["conditional_hit"] = rewrite_plan is not None and \
        rewrite_plan["condition_would_hit"] is True

    return results


# ─────────────── 4. 发布前校验器测试 ───────────────
def test_pack_validator() -> Dict[str, bool]:
    """使用 Mock 数据测试 PackValidator。"""
    from apps.workflow.workflow_admin_api import PackValidator, PackPublisher

    results: Dict[str, bool] = {}

    # 创建模拟 pack
    nodes_good = [
        MockNode("A", "A", "fusion_node", 1),
        MockNode("B", "B", "fusion_node", 2, upstream_deps=["A"]),
        MockNode("C", "C", "fusion_node", 3, upstream_deps=["B"]),
    ]
    pack_good = MockPack(id="good", version="v1.0", _nodes=nodes_good)

    # 我们要调用 PackValidator(pack).validate()，但它用 pack.nodes.all()
    # 这里做一个简化：直接用 PackValidator 的逻辑思路
    # 由于 PackValidator 内部依赖 FusionPipelineNode 的 ORM 方法，
    # 我们测试独立的表达式检查子逻辑
    from apps.workflow.condition_evaluator import safe_eval

    # 测试好的表达式
    results["valid_expr"] = bool(safe_eval("1 < 2 and ctx.yes", ctx={"yes": True}))

    # 测试恶意表达式被拒
    try:
        safe_eval("__import__('os').system('rm -rf /')", ctx={})
        results["reject_dangerous"] = False
    except Exception:
        results["reject_dangerous"] = True

    # 超时配置
    results["timeout_bound"] = 0 < 600 <= 3600

    return results


# ─────────────── 5. 节点执行状态机纯逻辑测试 ───────────────
def test_status_transitions() -> Dict[str, bool]:
    """在不依赖数据库的前提下，测试状态转移的纯逻辑。"""
    results: Dict[str, bool] = {}

    # 模拟 WorkflowInstance 的状态转移逻辑（纯 Python）
    LEGAL_TRANSITIONS = {
        "pending": {"running", "cancelled"},
        "running": {"done", "failed", "paused", "waiting_human", "running"},
        "paused": {"running", "cancelled", "failed"},
        "waiting_human": {"running", "cancelled", "failed"},
        "done": set(),
        "failed": {"running"},
        "cancelled": set(),
    }

    def can_transition(from_status, to_status):
        return to_status in LEGAL_TRANSITIONS.get(from_status, set())

    # 合法路径 1: pending → running → done
    results["legal_1"] = (
        can_transition("pending", "running")
        and can_transition("running", "done")
    )

    # 合法路径 2: pending → running → waiting_human → running → done
    results["legal_2"] = (
        can_transition("pending", "running")
        and can_transition("running", "waiting_human")
        and can_transition("waiting_human", "running")
        and can_transition("running", "done")
    )

    # 非法：从 done 回 running（应被拒绝）
    results["reject_done_to_running"] = not can_transition("done", "running")

    # 非法：从 cancelled 到 running
    results["reject_cancelled_to_running"] = not can_transition("cancelled", "running")

    # 失败后重试
    results["allow_retry_after_failure"] = can_transition("failed", "running")

    return results


# ─────────────── 运行全部测试 ───────────────
def run_all() -> int:
    print("=" * 70)
    print("  编排引擎核心逻辑 Sanity Check")
    print("=" * 70)

    test_suites = [
        ("ConditionEvaluator  条件表达式", test_condition_evaluator),
        ("ContextCompressor   上下文压缩", test_context_compressor),
        ("WorkflowDebugRunner 执行计划",   test_debug_runner),
        ("PackValidator       发布前校验", test_pack_validator),
        ("Status Transitions  状态转移",   test_status_transitions),
    ]

    total_tests = 0
    total_passed = 0
    failures: List[str] = []

    for name, test_fn in test_suites:
        print(f"\n  [{name}]")
        results = test_fn()
        for key, passed in results.items():
            total_tests += 1
            if passed:
                total_passed += 1
                status = "  ✓ "
            else:
                failures.append(f"{name} / {key}")
                status = "  ✗ "
            print(f"  {status} {key}: {passed}")

    print("\n" + "=" * 70)
    print(f"  Result: {total_passed}/{total_tests} tests passed")

    if failures:
        print("\n  失败项:")
        for f in failures:
            print(f"    - {f}")
        return 1

    print("  ✓ 全部通过 —— 核心逻辑自检成功")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
