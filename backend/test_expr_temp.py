# 测试每个表达式
from apps.workflow.condition_evaluator import safe_eval, ConditionSecurityError

def run(name, fn):
    try:
        result = fn()
        print(f"  ✓ {name}: {result}")
    except Exception as exc:
        print(f"  ✗ {name}: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()

print("=== 合法表达式 ===")
run("比较运算", lambda: safe_eval("ctx.score >= 60", ctx={"score": 80}))
run("布尔逻辑 and", lambda: safe_eval("ctx.topic == 'love' and ctx.episodes > 10", ctx={"topic": "love", "episodes": 30}))
run("in 运算", lambda: safe_eval("ctx.topic in ['love', 'suspense']", ctx={"topic": "love"}))
run("数学运算", lambda: safe_eval("ctx.a + ctx.b", ctx={"a": 2, "b": 3}))
run("Subscript 嵌套 (nodes 参数)",
    lambda: safe_eval("nodes['node_brief']['output']['quality_score'] >= 70",
                       nodes={"node_brief": {"output": {"quality_score": 85}}}))
run("属性访问 (ctx.nodes...)",
    lambda: safe_eval("ctx.nodes.node_brief.output.quality_score >= 70",
                       ctx={"nodes": {"node_brief": {"output": {"quality_score": 85}}}}))
run("三元 T", lambda: safe_eval("ctx.score >= 60 if ctx.has_script else False",
                                 ctx={"score": 80, "has_script": True}))
run("三元 F", lambda: safe_eval("ctx.score >= 60 if ctx.has_script else False",
                                 ctx={"score": 80, "has_script": False}))
run("空表达式", lambda: safe_eval(""))
run("None", lambda: safe_eval(None))

print("\n=== 危险表达式（应被拒绝）===")
for bad in [
    "__import__('os')",
    "open('/etc/passwd')",
    "lambda x: x.__class__.__mro__",
    "exec('a = 1')",
    "getattr(__builtins__, 'int')('123')",
]:
    try:
        safe_eval(bad)
        print(f"  ✗ 危险未拦截: {bad}")
    except ConditionSecurityError as exc:
        print(f"  ✓ SECURITY: {bad}")
    except Exception as exc:
        print(f"  ✓ 拒绝 {type(exc).__name__}: {bad}")
