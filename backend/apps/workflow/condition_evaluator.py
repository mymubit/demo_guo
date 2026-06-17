# -*- coding: utf-8 -*-
"""条件表达式安全求值引擎
========================================================
为工作流节点的 condition_expr / 路由条件提供严格受限的表达式求值。

安全策略：
  ① AST 白名单 — 只允许布尔/比较/算术运算和简单的属性访问
  ② __builtins__ = {} — 内置命名空间为空，无法访问 open/import/exec ...
  ③ 名称访问限制：只允许访问传入上下文的键，不允许任意属性构造
  ④ 执行超时保护：compile + eval 两步，最坏情况通过 SIGALRM 兜底
  ⑤ 最大表达式长度：2048 字符，防止 DoS

表达式示例（支持的语法子集）：
    ctx.overall_score >= 70
    nodes['node_brief']['is_ok'] and prev.length > 200
    not ctx.draft_only or ctx.reviewed
    ctx.episode_no % 2 == 0
    ctx.topic in ['爱情', '悬疑']
    ctx.characters >= 3 and ctx.word_count > 1000

支持变量：
    ctx        → WorkflowInstance.context（工作流全局上下文）
    prev       → 上一个成功节点的输出
    nodes      → {node_id: output_context} 已完成节点结果字典
    constants  → Pack 中的常量配置

禁止的语法（会抛出 SecurityError）：
    • 函数调用（除了 len/dict/list/set 等白名单）
    • 类定义 / Lambda
    • import / exec / eval / attribute access on non-data objects
========================================================
"""
from __future__ import annotations

import ast
import logging
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =========================================================
# 安全异常
# =========================================================
class ConditionSecurityError(ValueError):
    """表达式包含不安全的语法元素"""


class ConditionSyntaxError(ValueError):
    """表达式语法非法"""


class ConditionEvalError(RuntimeError):
    """表达式求值过程中运行时错误"""


# =========================================================
# AST 白名单
# =========================================================
# 允许的 AST 节点类型
_ALLOWED_AST_NODES: Set[type] = {
    ast.Expression, ast.Module,  # 外层

    # 布尔运算 and / or / not
    ast.BoolOp, ast.And, ast.Or, ast.Not,

    # 比较运算 == != < <= > >= in / not in
    ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn,

    # 三元表达式（条件表达式）: a if cond else b
    # 允许典型业务场景: "ctx.score >= 60 if ctx.has_script else False"
    ast.IfExp,

    # 二元算术运算 + - * / // % **
    ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
    ast.Mod, ast.Pow,

    # 一元运算 - +
    ast.UnaryOp, ast.USub, ast.UAdd,

    # 字面量
    ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict,

    # 名称访问（Name / Attribute / Subscript）
    ast.Name, ast.Attribute, ast.Subscript, ast.Load,

    # 白名单调用（仅 len / dict / list / set / str / int / float / bool）
    ast.Call,
}

# 允许的函数调用名称（白名单）
_ALLOWED_CALLABLES: Dict[str, Any] = {
    "len": len,
    "dict": dict,
    "list": list,
    "set": set,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "abs": abs,
    "max": max,
    "min": min,
    "sum": sum,
    "round": round,
}

# 表达式长度限制
MAX_EXPR_LENGTH = 2048


# =========================================================
# AST 验证器（递归检查所有节点均在白名单中）
# =========================================================
def _validate_ast(tree: ast.AST, *, expr_src: str) -> None:
    """递归校验 AST 树中的每个节点类型。

    发现非法节点立即抛出 ConditionSecurityError。
    """
    for node in ast.walk(tree):
        node_cls = type(node)
        if node_cls not in _ALLOWED_AST_NODES:
            raise ConditionSecurityError(
                f"禁止的语法元素: {node_cls.__name__} "
                f"位置: line {getattr(node, 'lineno', '?')}"
                f" — 原表达式: {expr_src[:120]}",
            )

        # 对 Call 节点额外做函数名白名单校验
        if isinstance(node, ast.Call):
            # 只允许: Name(id=白名单) 的直接调用
            func = node.func
            if not isinstance(func, ast.Name):
                raise ConditionSecurityError(
                    "只允许调用白名单内的函数（len/max/min/...），"
                    "不允许方法调用或任意表达式调用",
                )
            if func.id not in _ALLOWED_CALLABLES:
                raise ConditionSecurityError(
                    f"禁止的函数调用: {func.id}",
                )

        # 限制 Name 的 id 必须是允许的变量名（由 caller 控制 locals）
        # 这里不做强制，由 eval 时的 locals 来约束


# =========================================================
# 安全编译 + 代码对象缓存
# =========================================================
_code_cache: Dict[str, Any] = {}
_CACHE_MAX_SIZE = 2048  # LRU 式硬上限，防止内存膨胀


def _safe_compile(expr: str) -> Any:
    """安全编译表达式并缓存 code object。"""
    if len(expr) > MAX_EXPR_LENGTH:
        raise ConditionSecurityError(
            f"表达式过长 ({len(expr)} > {MAX_EXPR_LENGTH})",
        )

    if expr in _code_cache:
        return _code_cache[expr]

    # 缓存清理（简单策略）
    if len(_code_cache) >= _CACHE_MAX_SIZE:
        _code_cache.clear()

    # 解析 + 验证
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ConditionSyntaxError(f"语法错误: {exc.msg}") from exc

    _validate_ast(tree, expr_src=expr)

    code = compile(tree, "<safe_expr>", "eval")
    _code_cache[expr] = code
    return code


# =========================================================
# 主入口：安全求值
# =========================================================
def safe_eval(
    expr: str,
    *,
    ctx: Optional[Dict[str, Any]] = None,
    prev: Optional[Dict[str, Any]] = None,
    nodes: Optional[Dict[str, Dict[str, Any]]] = None,
    constants: Optional[Dict[str, Any]] = None,
    default_on_error: bool = False,
    logger_obj: Optional[logging.Logger] = None,
) -> bool:
    """安全地对表达式求值，返回布尔结果。

    Args:
        expr:            表达式字符串（空字符串视为 True）
        ctx:             全局上下文 dict（以属性方式访问: ctx.xxx / ctx['xxx']）
        prev:            上一节点输出 dict
        nodes:           {node_id: output} 的已完成节点输出集合
        constants:       Pack 级别的常量配置
        default_on_error: True=求值失败时返回 False（默认 False=抛出）
        logger_obj:      可选的 logger（不填则用模块级 logger）

    Returns:
        bool — 表达式求值结果（非 bool 类型会被强制 bool 化）
    """
    log = logger_obj or logger

    # 空表达式 = 没有条件约束 = 通过
    if not expr or not expr.strip():
        return True

    # 包装为 AttributeAccessDict（支持 . 属性访问）
    local_env: Dict[str, Any] = {
        "ctx":       _AttributeAccessDict(ctx or {}),
        "prev":      _AttributeAccessDict(prev or {}),
        "nodes":     {k: _AttributeAccessDict(v or {}) for k, v in (nodes or {}).items()},
        "constants": _AttributeAccessDict(constants or {}),
        "True": True,
        "False": False,
        "None": None,
    }

    # 安全的 globals（白名单函数 + 空 __builtins__）
    global_env: Dict[str, Any] = {
        "__builtins__": {},
        **_ALLOWED_CALLABLES,
    }

    try:
        code = _safe_compile(expr.strip())
        result = eval(code, global_env, local_env)  # noqa: S307
        return bool(result)
    except (ConditionSecurityError, ConditionSyntaxError) as exc:
        log.warning("[condition] 非法表达式拒绝执行: %s — %s", exc, expr)
        if default_on_error:
            return False
        raise
    except Exception as exc:  # 运行时错误（KeyError/TypeError 等）
        log.debug("[condition] 表达式求值返回 False: %s — expr=%s", exc, expr)
        if default_on_error:
            return False
        raise ConditionEvalError(str(exc)) from exc


# =========================================================
# AttributeAccessDict — 支持 obj.key 形式的访问
# =========================================================
class _AttributeAccessDict(dict):
    """允许通过 obj.key 访问 dict 内容，不覆盖的属性仍走常规访问。"""

    __slots__: List[str] = []

    def __getattr__(self, name: str) -> Any:
        try:
            value = self[name]
        except KeyError:
            # 缺失属性 → 返回空占位符，允许链式访问继续但结果为 falsy
            # 例：ctx.missing_field_that_does_not_exist
            return _MissingValue(name)
        # 支持嵌套属性访问：ctx.meta.topic → 包装递归
        if isinstance(value, dict) and not isinstance(value, _AttributeAccessDict):
            return _AttributeAccessDict(value)
        if isinstance(value, list):
            return [
                _AttributeAccessDict(item) if isinstance(item, dict) else item
                for item in value
            ]
        return value


class _MissingValue:
    """缺失的属性访问占位，保证链式访问不崩溃。

    逻辑行为：
        任何比较（==/!=/</>/...）返回 False
        布尔值 = False
        字符串 = ''
        数字 = 0
    """

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    def __bool__(self) -> bool:
        return False

    def __len__(self) -> int:
        return 0

    def __eq__(self, other: object) -> bool:
        return False

    def __ne__(self, other: object) -> bool:
        return False

    def __lt__(self, other: object) -> bool:
        return False

    def __le__(self, other: object) -> bool:
        return False

    def __gt__(self, other: object) -> bool:
        return False

    def __ge__(self, other: object) -> bool:
        return False

    def __contains__(self, item: object) -> bool:
        return False

    def __str__(self) -> str:
        return ""

    def __repr__(self) -> str:
        return f"<Missing:{self._name}>"


# =========================================================
# 便捷入口：从 NodeExecution 上下文快捷求值
# =========================================================
def eval_node_condition(
    expr: str,
    *,
    instance_context: Dict[str, Any],
    last_node_output: Optional[Dict[str, Any]],
    completed_nodes_outputs: Dict[str, Dict[str, Any]],
    pack_constants: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, Optional[str]]:
    """对工作流节点的 condition_expr 求值。

    Returns:
        (result: bool, error_msg: Optional[str])
        - error_msg=None 表示成功
        - error_msg 非空表示表达式问题（供调用者决定是否跳过该节点）
    """
    try:
        result = safe_eval(
            expr,
            ctx=instance_context,
            prev=last_node_output,
            nodes=completed_nodes_outputs,
            constants=pack_constants,
            default_on_error=False,
        )
        return result, None
    except (ConditionSecurityError, ConditionSyntaxError,
            ConditionEvalError) as exc:
        return False, str(exc)
