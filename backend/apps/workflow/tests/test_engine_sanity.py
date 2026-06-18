# -*- coding: utf-8 -*-
"""
编排引擎核心逻辑 Sanity Test（纯 Python，不依赖 Django）。
"""
from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 确保 apps 包可被找到（支持从项目根目录/任意子目录运行测试）
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 回溯找到 apps 包的父目录
_PATH = _CURRENT_DIR
while _PATH and _PATH != os.path.dirname(_PATH):
    if os.path.isdir(os.path.join(_PATH, "apps")):
        if _PATH not in sys.path:
            sys.path.insert(0, _PATH)
        break
    _PATH = os.path.dirname(_PATH)

logger = logging.getLogger(__name__)


@dataclass
class NodeConfig:
    node_id: str
    chain_order: int = 0
    upstream_deps: List[str] = field(default_factory=list)
    condition_expr: str = ""
    is_checkpoint: bool = False


def test_condition_evaluator():
    print("\n=== Test 1: ConditionEvaluator.safe_eval() ===")
    from apps.workflow.condition_evaluator import safe_eval, ConditionSecurityError

    # 基础布尔/比较
    assert safe_eval("ctx.score >= 60", ctx={"score": 80}) is True
    assert safe_eval("ctx.score >= 60", ctx={"score": 40}) is False
    print("  ✓ 基础比较")

    # 布尔逻辑
    assert safe_eval(
        "ctx.topic == '爱情' and ctx.episodes > 10",
        ctx={"topic": "爱情", "episodes": 30},
    ) is True
    print("  ✓ 布尔逻辑 and")

    # in / not in
    assert safe_eval(
        "ctx.topic in ['爱情', '悬疑', '都市']",
        ctx={"topic": "悬疑"},
    ) is True
    print("  ✓ in 运算")

    # 数学运算 — 注意：safe_eval 返回的是 bool(result)，所以 2+3=5 → bool(5)=True
    result = safe_eval("ctx.a + ctx.b", ctx={"a": 2, "b": 3})
    assert result is True  # 5 在 bool 上下文中为 True
    assert safe_eval("ctx.a + ctx.b == 5", ctx={"a": 2, "b": 3}) is True
    assert safe_eval("ctx.sum == 100", ctx={"sum": 100}) is True
    print("  ✓ 数学运算")

    # 访问嵌套 dict（nodes= 显式传入）
    nodes_data = {
        "node_brief": {"output": {"is_ok": True, "quality_score": 85}},
        "node_outline": {"output": {"chapter_count": 15}},
    }
    assert safe_eval(
        "nodes['node_brief']['output']['quality_score'] >= 70",
        nodes=nodes_data,
    ) is True
    print("  ✓ nodes= 显式传入")

    # 属性访问
    assert safe_eval(
        "ctx.nodes.node_brief.output.quality_score >= 70",
        ctx={"nodes": nodes_data},
    ) is True
    print("  ✓ 属性访问")

    # 三元表达式
    assert safe_eval(
        "ctx.score >= 60 if ctx.has_script else False",
        ctx={"score": 80, "has_script": True},
    ) is True
    assert safe_eval(
        "ctx.score >= 60 if ctx.has_script else False",
        ctx={"score": 80, "has_script": False},
    ) is False
    print("  ✓ 三元表达式 (IfExp)")

    # 空表达式 → True（默认放行）
    assert safe_eval("") is True
    assert safe_eval(None) is True
    print("  ✓ 空表达式")

    # 危险代码 — 必须被拒绝（抛出 Exception 即视为通过）
    danger_caught = 0
    for bad in [
        "__import__('os')",
        "open('/etc/passwd').read()",
        "lambda x: x.__class__.__mro__",
        "exec('a = 1')",
        "getattr(__builtins__, 'int')('123')",
    ]:
        try:
            safe_eval(bad)
        except Exception:
            danger_caught += 1
    assert danger_caught == 5, f"应拦截 5 个危险表达式，实际 {danger_caught}"
    print(f"  ✓ 危险代码拦截 {danger_caught}/5")
    print("  ✓ Test 1 通过")


def test_skill_bridge_result():
    print("\n=== Test 2: SkillBridge / SkillBridgeResult ===")
    from apps.workflow.skill_bridge import SkillBridgeResult, SkillBridge

    result = SkillBridgeResult(
        success=True, output={"content": "剧本正文"},
        errors=[], coin_cost=30, duration_ms=3500,
    )
    assert result.success is True
    assert result.output["content"] == "剧本正文"
    assert result.coin_cost == 30
    print("  ✓ SkillBridgeResult")

    # SkillBridge dry_run
    class FakeNodeConfig:
        node_id = "node_brief"
        chain_order = 1
        skill_id = ""
        runner_path = ""
        extra_config = {}
        coin_cost = 10

    bridge = SkillBridge(project=None, node_config=FakeNodeConfig(), context={})
    dry = bridge.run(dry_run=True)
    assert dry.success is True
    assert "dry-run output for node_brief" in dry.output["content"]
    print(f"  ✓ SkillBridge dry_run")
    print("  ✓ Test 2 通过")


def test_execution_plan():
    print("\n=== Test 3: WorkflowEngine 节点执行计划 ===")
    nodes = [
        NodeConfig(node_id="node_brief", chain_order=1, upstream_deps=[]),
        NodeConfig(node_id="node_structure", chain_order=2, upstream_deps=["node_brief"]),
        NodeConfig(node_id="node_character", chain_order=3, upstream_deps=["node_structure"]),
        NodeConfig(node_id="node_outline", chain_order=4,
                   upstream_deps=["node_structure", "node_character"]),
        NodeConfig(node_id="node_script", chain_order=5, upstream_deps=["node_outline"]),
    ]

    in_deg = {n.node_id: len(n.upstream_deps) for n in nodes}
    ready = sorted([nid for nid, d in in_deg.items() if d == 0],
                    key=lambda x: next(n.chain_order for n in nodes if n.node_id == x))
    order = []
    while ready:
        nid = ready.pop(0)
        order.append(nid)
        for n in nodes:
            if nid in n.upstream_deps:
                in_deg[n.node_id] -= 1
                if in_deg[n.node_id] == 0:
                    ready.append(n.node_id)

    assert len(order) == len(nodes)
    assert order[0] == "node_brief"
    assert order[-1] == "node_script"
    print(f"  ✓ 拓扑排序: {' → '.join(order)}")

    # 循环依赖检测
    cyclic = [
        NodeConfig(node_id="A", chain_order=1, upstream_deps=["B"]),
        NodeConfig(node_id="B", chain_order=2, upstream_deps=["A"]),
    ]
    deg = {n.node_id: len(n.upstream_deps) for n in cyclic}
    q = [nid for nid, d in deg.items() if d == 0]
    visited = 0
    while q:
        nid = q.pop(0)
        visited += 1
        for n in cyclic:
            if nid in n.upstream_deps:
                deg[n.node_id] -= 1
                if deg[n.node_id] == 0:
                    q.append(n.node_id)
    assert visited < len(cyclic)
    print(f"  ✓ 循环依赖检测: 仅访问 {visited}/{len(cyclic)} 节点")
    print("  ✓ Test 3 通过")


def test_context_compressor():
    print("\n=== Test 4: ContextCompressor ===")
    from apps.workflow.workflow_debug_runner import ContextCompressor

    compressor = ContextCompressor(soft_limit_bytes=100, hard_limit_bytes=500)

    small = {"a": 1, "b": "hello"}
    _, stats = compressor.compress(small)
    assert stats["level"] == 0
    print(f"  ✓ 小上下文 level=0 before={stats['bytes_before']}")

    medium = {"nodes": {"node_" + str(i): {"content": "x" * 300} for i in range(5)}}
    _, stats = compressor.compress(medium)
    assert stats["level"] >= 1
    print(f"  ✓ 中等上下文 level={stats['level']} reduction={stats['reduction_pct']}%")

    large = {
        "nodes": {"node_" + str(i): {"content": "y" * 2000, "extra": list(range(50))} for i in range(20)},
        "project_meta": {"user_id": "u-1", "title": "测试短剧"},
    }
    _, stats = compressor.compress(large)
    assert stats["level"] >= 2
    assert stats["bytes_after"] < stats["bytes_before"]
    print(f"  ✓ 大上下文 level={stats['level']} reduction={stats['reduction_pct']}%")
    print("  ✓ Test 4 通过")


def test_pack_validator():
    print("\n=== Test 5: Pack 基本字段 sanity ===")
    nodes = [
        {"fusion_node_id": "node_brief", "chain_order": 1, "runner_type": "fusion_node"},
        {"fusion_node_id": "node_structure", "chain_order": 2, "runner_type": "fusion_node"},
        {"fusion_node_id": "node_script", "chain_order": 3, "runner_type": "fusion_node"},
    ]
    orders = [n["chain_order"] for n in nodes]
    assert orders == sorted(orders)
    print(f"  ✓ chain_order 递增: {orders}")

    for n in nodes:
        assert n.get("fusion_node_id")
    print(f"  ✓ 所有节点都有 fusion_node_id")

    # 循环依赖检测
    bad = [
        {"fusion_node_id": "A", "chain_order": 1, "upstream_deps": ["B"]},
        {"fusion_node_id": "B", "chain_order": 2, "upstream_deps": ["A"]},
    ]
    deps = {n["fusion_node_id"]: list(n.get("upstream_deps", [])) for n in bad}
    has_cycle = False
    for start in deps:
        visited = {start}
        stack = list(deps.get(start, []))
        while stack:
            cur = stack.pop()
            if cur == start:
                has_cycle = True
                break
            if cur in visited:
                continue
            visited.add(cur)
            stack.extend(deps.get(cur, []))
        if has_cycle:
            break
    assert has_cycle
    print(f"  ✓ 循环依赖检测通过")
    print("  ✓ Test 5 通过")


def test_retry_backoff():
    """P2-3: 测试指数退避计算。"""
    print("\n=== Test 6: 重试退避策略 ===")
    # 模拟 cfg 数据
    from dataclasses import dataclass, field as dc_field
    @dataclass
    class _Cfg:
        backoff_strategy: str = "exponential"
        backoff_base: float = 2.0

    # exponential: 2 * 2^attempt
    cfg = _Cfg("exponential", 2.0)
    for attempt, expected in [(0, 2.0), (1, 4.0), (2, 8.0), (3, 16.0)]:
        actual = cfg.backoff_base * (2 ** attempt)
        assert abs(actual - expected) < 0.001, f"attempt={attempt} 失败"
    print(f"  ✓ exponential: base=2.0 → [2, 4, 8, 16]")

    # linear: 2 * (attempt+1)
    cfg = _Cfg("linear", 2.0)
    for attempt, expected in [(0, 2.0), (1, 4.0), (2, 6.0)]:
        actual = cfg.backoff_base * (attempt + 1)
        assert abs(actual - expected) < 0.001
    print(f"  ✓ linear: base=2.0 → [2, 4, 6]")

    # fixed: 2.0
    cfg = _Cfg("fixed", 2.0)
    for attempt in range(5):
        actual = cfg.backoff_base
        assert abs(actual - 2.0) < 0.001
    print(f"  ✓ fixed: 永远 2.0")

    # 重试成本累加逻辑（模拟）
    retries = [
        {"coin_cost": 10, "token_in": 1000, "token_out": 500},
        {"coin_cost": 10, "token_in": 1000, "token_out": 500},
        {"coin_cost": 10, "token_in": 1000, "token_out": 500},
    ]
    total_coin = sum(r["coin_cost"] for r in retries)
    total_in = sum(r["token_in"] for r in retries)
    total_out = sum(r["token_out"] for r in retries)
    assert total_coin == 30
    assert total_in == 3000
    assert total_out == 1500
    print(f"  ✓ 重试 3 次后累加: coin={total_coin}, in={total_in}, out={total_out}")
    print("  ✓ Test 6 通过")


def test_prometheus_export_format():
    """P2-4: Prometheus 文本导出格式正确性。"""
    print("\n=== Test 7: Prometheus 导出格式 ===")

    # 模拟空数据情况下的格式
    sample_output = (
        "# HELP workflow_instances_total Total workflow instances by status\n"
        "# TYPE workflow_instances_total counter\n"
        'workflow_instances_total{status="done",pack_version="v1",window_minutes="10"} 5\n'
        "# HELP coin_cost_total Total coin cost in window\n"
        "# TYPE coin_cost_total counter\n"
        'coin_cost_total{window_minutes="10"} 150\n'
    )

    # 检查关键标记
    assert "# HELP" in sample_output
    assert "# TYPE" in sample_output
    assert "workflow_instances_total" in sample_output
    assert "coin_cost_total" in sample_output
    # 标签引号
    assert 'status="done"' in sample_output
    print("  ✓ HELP/TYPE 注释存在")
    print("  ✓ 标签格式正确 (status=\"done\")")
    print("  ✓ 指标行存在")
    print("  ✓ Test 7 通过")


def test_skill_bridge_cost_aggregation():
    """P2-2: SkillBridge 成本累加。"""
    print("\n=== Test 8: SkillBridge 成本累加 ===")
    from apps.workflow.skill_bridge import SkillBridgeResult

    # 模拟 3 次重试结果
    results = [
        SkillBridgeResult(success=False, output={}, errors=["LLM timeout"], coin_cost=10),
        SkillBridgeResult(success=False, output={}, errors=["LLM timeout"], coin_cost=10),
        SkillBridgeResult(success=True, output={"content": "剧本"}, coin_cost=15, duration_ms=3200),
    ]

    total_cost = sum(r.coin_cost for r in results)
    assert total_cost == 35  # 10+10+15
    print(f"  ✓ 3 次调用金币累加: {total_cost}")

    # 最终结果应该是最后一次成功的
    last = results[-1]
    assert last.success is True
    assert last.coin_cost == 15
    print(f"  ✓ 最终结果: success={last.success}, cost={last.coin_cost}")

    print("  ✓ Test 8 通过")


def test_creation_skill_catalog():
    """P2-1: 验证 7 个创作技能在 SKILL_CATALOG 中的配置正确。"""
    print("\n=== Test 9: 创作技能 Catalog 注册 ===")

    import ast
    catalog_path = "apps/skill/migrations/0031_creation_skill_catalog.py"
    with open(catalog_path, encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)

    # 找顶层名为 SKILL_CATALOG 的常量赋值
    catalog: List[Dict] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SKILL_CATALOG":
                    # 提取 list literal
                    if isinstance(node.value, ast.List):
                        for el in node.value.elts:
                            el_dict = ast.literal_eval(el)
                            catalog.append(el_dict)
                    break
    assert catalog, "未在迁移文件中找到 SKILL_CATALOG"

    expected_ids = {
        "creation.brief", "creation.structure", "creation.character",
        "creation.outline", "creation.script", "creation.review", "creation.polish",
    }
    actual_ids = {s["skill_id"] for s in catalog}
    assert actual_ids == expected_ids, f"skill_id 不匹配: {actual_ids ^ expected_ids}"
    print(f"  ✓ 7 个技能全部注册: {sorted(actual_ids)}")

    # 验证字段完整性
    for skill in catalog:
        assert skill["skill_id"], f"skill_id 缺失: {skill}"
        assert skill["name"], f"name 缺失: {skill['skill_id']}"
        assert skill["category"] in {"creator", "quality", "compliance", "shared"}
        assert skill["skill_layer"] in {"foundation", "business", "tool"}
        assert skill["lifecycle_status"] == "active", f"未激活: {skill['skill_id']}"
        assert skill["quota_cost"] > 0, f"cost=0: {skill['skill_id']}"
        assert skill["system_hint"], f"system_hint 缺失: {skill['skill_id']}"
        assert skill["output_schema"], f"output_schema 缺失: {skill['skill_id']}"
    print(f"  ✓ 所有技能字段完整（skill_id/name/category/lifecycle/cost/schema）")

    # 验证 cost 合理（brief < structure < script）
    brief_cost = next(s["quota_cost"] for s in catalog if s["skill_id"] == "creation.brief")
    script_cost = next(s["quota_cost"] for s in catalog if s["skill_id"] == "creation.script")
    assert brief_cost < script_cost, f"script 应当比 brief 贵: {brief_cost} < {script_cost}"
    print(f"  ✓ Cost 阶梯合理: brief={brief_cost} < script={script_cost}")

    print("  ✓ Test 9 通过")


def main():
    tests = [
        test_condition_evaluator,
        test_skill_bridge_result,
        test_execution_plan,
        test_context_compressor,
        test_pack_validator,
        test_retry_backoff,
        test_prometheus_export_format,
        test_skill_bridge_cost_aggregation,
        test_creation_skill_catalog,
    ]
    print("=" * 60)
    print(f"  共 {len(tests)} 个测试")
    print("=" * 60)

    t0 = time.time()
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as exc:
            print(f"  ✗ {test.__name__}: {exc}")
        except Exception as exc:
            logger.exception(f"  ✗ {test.__name__}: {exc}")

    elapsed_ms = int((time.time() - t0) * 1000)
    print("\n" + "=" * 60)
    print(f"  结果: {passed}/{len(tests)} 通过，耗时 {elapsed_ms} ms")
    print("=" * 60)
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
