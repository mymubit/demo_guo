from apps.workflow.condition_evaluator import safe_eval, ConditionSecurityError

# 模拟测试文件中 test_condition_evaluator 的逻辑
print("Testing condition evaluator assertions...")

# 1) 基础布尔/比较
assert safe_eval("ctx.score >= 60", ctx={"score": 80}) is True, "比较运算"
assert safe_eval("ctx.score >= 60", ctx={"score": 40}) is False
print("OK: 基础布尔/比较")

# 2) 布尔逻辑
assert safe_eval("ctx.topic == '爱情' and ctx.episodes > 10",
                 ctx={"topic": "爱情", "episodes": 30}) is True
print("OK: 布尔逻辑")

# 3) in / not in
assert safe_eval("ctx.topic in ['爱情', '悬疑', '都市']",
                 ctx={"topic": "悬疑"}) is True
print("OK: in 运算")

# 4) 数学运算
assert safe_eval("ctx.a + ctx.b", ctx={"a": 2, "b": 3}) == 5
print("OK: 数学运算")

# 5) 嵌套 dict - nodes 参数
nodes_data = {
    "node_brief": {"output": {"is_ok": True, "quality_score": 85}},
    "node_outline": {"output": {"chapter_count": 15}},
}
assert safe_eval("nodes['node_brief']['output']['quality_score'] >= 70",
                 nodes=nodes_data) is True
print("OK: Subscript 嵌套 nodes 参数")

# 6) 属性访问
assert safe_eval("ctx.nodes.node_brief.output.quality_score >= 70",
                 ctx={"nodes": nodes_data}) is True
print("OK: 属性访问")

# 7) 三元表达式
assert safe_eval("ctx.score >= 60 if ctx.has_script else False",
                 ctx={"score": 80, "has_script": True}) is True
assert safe_eval("ctx.score >= 60 if ctx.has_script else False",
                 ctx={"score": 80, "has_script": False}) is False
print("OK: 三元表达式")

# 8) 空表达式
assert safe_eval("") is True
assert safe_eval(None) is True
print("OK: 空表达式")

# 9) 危险代码 - 应抛出 SecurityError 或其他异常
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
        print(f"  ✗ 危险表达式未拦截: {bad}")
    except Exception:
        danger_caught += 1

assert danger_caught == 5, f"应拦截 5 个危险表达式，实际 {danger_caught}"
print(f"OK: 危险代码拦截 {danger_caught}/5")

print("\n✓ 全部断言通过")
