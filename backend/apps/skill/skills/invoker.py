# -*- coding: utf-8 -*-
"""
统一技能调用引擎（SkillInvoker）

所有技能调用统一经由此入口，保障：
1. 统一入参校验（input_schema）
2. 统一错误处理与重试
3. 统一配额扣减与回补
4. 统一执行轨迹记录（LLMUsageLog + AgentExecutionRun）
5. 统一降级熔断机制

使用方式：
    from apps.skill.skills.invoker import SkillInvoker, get_skill_invoker

    invoker = get_skill_invoker()
    result = invoker.invoke(
        skill_id="brief.project_definition",
        payload={"theme": "family-revenge", "core_idea": "..."},
        project_id=project.id,
        user_id=user.id,
    )
"""
from __future__ import annotations

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ============================================================
# 数据结构
# ============================================================

class SkillResult:
    """
    统一技能调用结果。

    标准化结构，所有技能 invoke 返回此类型：
    - success=True 时 data 为技能输出（字典）
    - success=False 时 error 含错误信息
    - meta 含调用元数据（耗时、配额消耗、trace_id）
    """

    def __init__(
        self,
        skill_id: str,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        self.skill_id = skill_id
        self.success = success
        self.data = data
        self.error = error or {}
        self.meta = meta or {}
        self.trace_id: str = self.meta.get("trace_id", "")
        self.duration_ms: float = self.meta.get("duration_ms", 0.0)
        self.quota_cost: float = self.meta.get("quota_cost", 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "meta": self.meta,
        }

    @classmethod
    def ok(cls, skill_id: str, data: Dict[str, Any], **meta) -> "SkillResult":
        return cls(skill_id=skill_id, success=True, data=data, meta=meta)

    @classmethod
    def fail(cls, skill_id: str, code: int, message: str, **meta) -> "SkillResult":
        return cls(
            skill_id=skill_id,
            success=False,
            error={"code": code, "message": message},
            meta=meta,
        )


@dataclass
class SkillInvokeContext:
    """技能调用上下文，贯穿整个 invoke 链路。"""
    skill_id: str
    project_id: Optional[str] = None
    user_id: Optional[int] = None
    skill_definition: Any = None          # AgentSkillDefinition 对象（lazy load）
    payload: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    retry_attempt: int = 0                # 当前重试次数
    started_at: float = field(default_factory=time.time)

    # 运行时填充
    quota_cost: float = 0.0
    duration_ms: float = 0.0


# ============================================================
# 错误码快捷引用（避免循环 import）
# ============================================================

def _skill_error_codes():
    from apps.common.exceptions import (
        SKILL_NOT_FOUND, SKILL_DISABLED, SKILL_LIFECYCLE_ERROR,
        SKILL_VALIDATION_ERROR, SKILL_TIMEOUT, SKILL_RATE_LIMIT,
        SKILL_PROVIDER_ERROR, SKILL_INTERNAL_ERROR, SKILL_QUOTA_EXCEEDED,
        SKILL_FALLBACK_FAILED, SKILL_CIRCUIT_BREAK,
    )
    return dict(
        SKILL_NOT_FOUND=SKILL_NOT_FOUND,
        SKILL_DISABLED=SKILL_DISABLED,
        SKILL_LIFECYCLE_ERROR=SKILL_LIFECYCLE_ERROR,
        SKILL_VALIDATION_ERROR=SKILL_VALIDATION_ERROR,
        SKILL_TIMEOUT=SKILL_TIMEOUT,
        SKILL_RATE_LIMIT=SKILL_RATE_LIMIT,
        SKILL_PROVIDER_ERROR=SKILL_PROVIDER_ERROR,
        SKILL_INTERNAL_ERROR=SKILL_INTERNAL_ERROR,
        SKILL_QUOTA_EXCEEDED=SKILL_QUOTA_EXCEEDED,
        SKILL_FALLBACK_FAILED=SKILL_FALLBACK_FAILED,
        SKILL_CIRCUIT_BREAK=SKILL_CIRCUIT_BREAK,
    )


# ============================================================
# 入参校验
# ============================================================

def _validate_payload(ctx: SkillInvokeContext) -> Optional[SkillResult]:
    """校验 payload 是否符合 skill 的 input_schema。返回 None 表示通过。"""
    import jsonschema

    schema = ctx.skill_definition.input_schema
    if not schema:
        return None
    try:
        jsonschema.validate(instance=ctx.payload, schema=schema)
        return None
    except jsonschema.ValidationError as exc:
        from apps.common.exceptions import SKILL_VALIDATION_ERROR
        return SkillResult.fail(
            ctx.skill_id,
            code=SKILL_VALIDATION_ERROR,
            message=f"入参校验失败：{exc.message}",
            trace_id=ctx.trace_id,
        )


# ============================================================
# 技能生命周期校验
# ============================================================

def _check_lifecycle(ctx: SkillInvokeContext) -> Optional[SkillResult]:
    """检查技能生命周期状态是否允许调用。返回 None 表示通过。"""
    codes = _skill_error_codes()
    skill = ctx.skill_definition
    status = skill.lifecycle_status

    if status == skill.LIFECYCLE_DRAFT:
        return SkillResult.fail(
            ctx.skill_id,
            code=codes["SKILL_LIFECYCLE_ERROR"],
            message=f"技能 {ctx.skill_id} 尚未发布（draft），暂不可用",
            trace_id=ctx.trace_id,
        )
    if status == skill.LIFECYCLE_DEPRECATED:
        return SkillResult.fail(
            ctx.skill_id,
            code=codes["SKILL_DISABLED"],
            message=f"技能 {ctx.skill_id} 已废弃",
            trace_id=ctx.trace_id,
        )
    if status == skill.LIFECYCLE_GRAY:
        # 灰度分流：按 gray_weight 决定是否命中
        import random
        if random.randint(1, 100) > skill.gray_weight:
            return SkillResult.fail(
                ctx.skill_id,
                code=codes["SKILL_LIFECYCLE_ERROR"],
                message="当前灰度流量未覆盖此技能",
                trace_id=ctx.trace_id,
            )
    return None


# ============================================================
# 配额校验与扣减
# ============================================================

def _check_and_charge_quota(ctx: SkillInvokeContext) -> Optional[SkillResult]:
    """检查并预扣配额。返回 None 表示通过；返回 SkillResult.fail 表示配额不足。"""
    codes = _skill_error_codes()
    if ctx.payload.get("skip_skill_quota"):
        return None

    cost = int(ctx.quota_cost or 0)
    if cost <= 0:
        return None

    if ctx.user_id is None:
        return None

    try:
        from django.contrib.auth import get_user_model
        from django.core.exceptions import PermissionDenied

        from apps.billing.services import BillingService, InsufficientCoins

        user = get_user_model().objects.get(pk=ctx.user_id)
        BillingService.charge(
            user,
            "skill.invoke",
            reference_id=f"skill_pre_{ctx.trace_id}",
            remark=f"技能调用：{ctx.skill_id}",
            coin_cost=cost,
        )
        return None
    except InsufficientCoins as exc:
        return SkillResult.fail(
            ctx.skill_id,
            code=codes["SKILL_QUOTA_EXCEEDED"],
            message=str(exc) or "配额不足",
            trace_id=ctx.trace_id,
        )
    except PermissionDenied as exc:
        return SkillResult.fail(
            ctx.skill_id,
            code=codes["SKILL_QUOTA_EXCEEDED"],
            message=str(exc) or "配额不足",
            trace_id=ctx.trace_id,
        )
    except Exception as exc:
        logger.warning("[SkillInvoker] 配额检查失败: %s", exc)
        return SkillResult.fail(
            ctx.skill_id,
            code=codes["SKILL_QUOTA_EXCEEDED"],
            message="配额校验失败",
            trace_id=ctx.trace_id,
        )


def _refund_quota(ctx: SkillInvokeContext) -> None:
    """配额回补（技能执行失败时调用）。"""
    if ctx.payload.get("skip_skill_quota"):
        return
    cost = int(ctx.quota_cost or 0)
    if cost <= 0 or ctx.user_id is None:
        return
    reference_id = f"skill_pre_{ctx.trace_id}"
    try:
        from django.contrib.auth import get_user_model

        from apps.billing.models import CoinLedger
        from apps.billing.services import BillingService

        user = get_user_model().objects.get(pk=ctx.user_id)
        if CoinLedger.objects.filter(
            user=user,
            reference_id=reference_id,
            delta__gt=0,
        ).exists():
            return
        BillingService.credit(
            user,
            cost,
            action_key="ai.generate.refund",
            reference_id=reference_id,
            remark=f"技能失败回补：{ctx.skill_id}",
            entry_type=CoinLedger.TYPE_REFUND,
        )
    except Exception as exc:
        logger.warning("[SkillInvoker] 配额回补失败: %s", exc)


# ============================================================
# LLM 调用核心
# ============================================================

def _resolve_llm_route_key(skill_id: str) -> str:
    """creation.* 技能 ID → AgentLlmRouteConfig.route_key。"""
    mapping = {
        "creation.brief": "brief",
        "creation.structure": "world",
        "creation.character": "character",
        "creation.outline": "outline",
        "creation.script": "script",
        "creation.review": "review",
        "creation.polish": "polish",
    }
    if skill_id in mapping:
        return mapping[skill_id]
    if skill_id.startswith("creation."):
        return skill_id.split(".", 1)[1]
    return skill_id


def _call_llm_for_skill(ctx: SkillInvokeContext) -> Dict[str, Any]:
    """
    调用 LLM 执行技能。

    流程：
    1. 从 AgentSkillDefinition 读取 system_hint
    2. 从 AgentLlmRouteConfig 读取 LLM Provider
    3. 组装 prompt 并调用 LlmService.generate_json
    4. 解析输出并按 output_schema 校验
    """
    skill = ctx.skill_definition
    system_hint = skill.system_hint or ""
    user_prompt = _build_user_prompt(ctx)

    from apps.agent.routes import AgentLlmRouteService
    from apps.creation.monitoring.execution_run_service import get_active_run_id
    from apps.skill.llm.chat import LlmService, LlmServiceError
    from apps.skill.llm.usage_log import llm_usage_scope
    from apps.skill.models import LlmUsageLog

    route_key = _resolve_llm_route_key(ctx.skill_id)
    provider_id = AgentLlmRouteService.resolve_provider_id(route_key)
    max_tokens = AgentLlmRouteService.resolve_max_tokens(route_key) or 8192
    temperature = 0.7

    try:
        with llm_usage_scope(
            source_type=LlmUsageLog.SOURCE_AGENT,
            source_key=ctx.skill_id[:64],
            project_id=ctx.project_id,
            user_id=ctx.user_id,
            execution_run_id=get_active_run_id(),
            sub_skill_id=ctx.skill_id[:64],
        ):
            data = LlmService.generate_json(
                system_prompt=system_hint,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                provider_id=provider_id,
                upstream=ctx.payload if isinstance(ctx.payload, dict) else {"payload": ctx.payload},
                trace_extra={"skill_id": ctx.skill_id},
            )
    except LlmServiceError as exc:
        raise LlmCallError(str(exc)) from exc

    if not isinstance(data, dict):
        return {"content": str(data), "raw": True}

    schema = skill.output_schema
    if schema:
        import jsonschema

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as exc:
            logger.warning(
                "[SkillInvoker] output_schema 校验失败 skill=%s: %s",
                ctx.skill_id,
                exc.message,
            )

    return data


class LlmCallError(Exception):
    """LLM 调用失败。"""
    pass


def _build_user_prompt(ctx: SkillInvokeContext) -> str:
    """将 payload 组装为用户提示词。"""
    import json
    payload_str = json.dumps(ctx.payload, ensure_ascii=False, indent=2)
    return f"请根据以下输入参数执行技能 {ctx.skill_id}：\n\n{payload_str}"


def _parse_skill_output(ctx: SkillInvokeContext, raw: str) -> Dict[str, Any]:
    """解析 LLM 输出的 JSON，校验 output_schema。"""
    import json
    import jsonschema

    # 尝试从 markdown 代码块中提取 JSON
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        json_lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(json_lines)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 非 JSON 输出，按纯文本处理
        return {"content": raw, "raw": True}

    # 按 output_schema 校验
    schema = ctx.skill_definition.output_schema
    if schema:
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as exc:
            logger.warning(
                "[SkillInvoker] output_schema 校验失败 skill=%s: %s",
                ctx.skill_id, exc.message,
            )
            # 校验失败不阻断，仍返回数据，仅记录警告

    return data


# ============================================================
# 重试与降级
# ============================================================

def _execute_with_retry(ctx: SkillInvokeContext) -> SkillResult:
    """
    执行技能调用（含重试 + 降级逻辑）。

    重试策略来源：AgentSkillDefinition.retry_policy
    降级策略来源：AgentSkillDefinition.fallback_skill_id
    """
    codes = _skill_error_codes()
    skill = ctx.skill_definition
    retry_policy = skill.retry_policy or {}
    max_attempts = int(retry_policy.get("max_attempts", 1))
    backoff_seconds = float(retry_policy.get("backoff_seconds", 5.0))

    last_error: Optional[SkillResult] = None

    for attempt in range(1, max_attempts + 1):
        ctx.retry_attempt = attempt - 1
        result = _do_invoke(ctx)

        if result.success:
            return result

        error_code = result.error.get("code", 0)

        # 非可重试错误（P0）
        if error_code in (
            codes["SKILL_NOT_FOUND"],
            codes["SKILL_DISABLED"],
            codes["SKILL_LIFECYCLE_ERROR"],
            codes["SKILL_VALIDATION_ERROR"],
            codes["SKILL_QUOTA_EXCEEDED"],
            codes["SKILL_CIRCUIT_BREAK"],
        ):
            return result

        last_error = result

        # 可重试错误（P1）— 指数退避
        if attempt < max_attempts:
            wait = backoff_seconds * (2 ** (attempt - 1))
            logger.info(
                "[SkillInvoker] 重试 skill=%s attempt=%s wait=%.1fs code=%s",
                ctx.skill_id, attempt, wait, error_code,
            )
            time.sleep(wait)

    # 降级
    if skill.fallback_skill_id:
        logger.info("[SkillInvoker] 降级到 fallback=%s", skill.fallback_skill_id)
        ctx.skill_id = skill.fallback_skill_id
        # 重新加载 fallback 技能的 definition
        ctx.skill_definition = _load_skill_definition(skill.fallback_skill_id)
        if ctx.skill_definition is None:
            return SkillResult.fail(
                skill.fallback_skill_id,
                code=codes["SKILL_FALLBACK_FAILED"],
                message="降级技能不存在",
                trace_id=ctx.trace_id,
            )
        fallback_result = _execute_with_retry(ctx)
        if fallback_result.success:
            fallback_result.meta["fallback_from"] = skill.skill_id
            return fallback_result
        return SkillResult.fail(
            skill.fallback_skill_id,
            code=codes["SKILL_FALLBACK_FAILED"],
            message="降级技能执行失败",
            trace_id=ctx.trace_id,
            original_error=last_error.to_dict() if last_error else None,
        )

    return last_error or SkillResult.fail(
        ctx.skill_id,
        code=codes["SKILL_INTERNAL_ERROR"],
        message="技能执行失败且无可用降级方案",
        trace_id=ctx.trace_id,
    )


# ============================================================
# 核心 invoke 流程
# ============================================================

def _do_invoke(ctx: SkillInvokeContext) -> SkillResult:
    """
    实际执行技能（不含重试），供 _execute_with_retry 调用。
    """
    codes = _skill_error_codes()
    skill = ctx.skill_definition

    try:
        # 1. 入参校验
        err = _validate_payload(ctx)
        if err:
            return err

        # 2. 技能实际执行
        output = _call_llm_for_skill(ctx)

        # 3. 配额确认扣减（precharge 已在前面完成，这里只记录）
        ctx.quota_cost = float(skill.quota_cost or 0)
        ctx.duration_ms = (time.time() - ctx.started_at) * 1000

        # 4. 写入执行轨迹
        _write_execution_trace(ctx, success=True)

        return SkillResult.ok(
            skill_id=ctx.skill_id,
            data=output,
            trace_id=ctx.trace_id,
            duration_ms=ctx.duration_ms,
            quota_cost=ctx.quota_cost,
            retry_attempt=ctx.retry_attempt,
        )

    except LlmCallError as exc:
        ctx.duration_ms = (time.time() - ctx.started_at) * 1000
        _write_execution_trace(ctx, success=False, error=str(exc))
        # 判断错误类型
        err_str = str(exc).lower()
        if "timeout" in err_str or "timed out" in err_str:
            code = codes["SKILL_TIMEOUT"]
        elif "rate limit" in err_str or "429" in err_str:
            code = codes["SKILL_RATE_LIMIT"]
        elif "provider" in err_str or "connection" in err_str:
            code = codes["SKILL_PROVIDER_ERROR"]
        else:
            code = codes["SKILL_PROVIDER_ERROR"]
        return SkillResult.fail(ctx.skill_id, code=code, message=str(exc), trace_id=ctx.trace_id)

    except Exception as exc:
        ctx.duration_ms = (time.time() - ctx.started_at) * 1000
        _write_execution_trace(ctx, success=False, error=str(exc))
        logger.exception("[SkillInvoker] 技能执行异常 skill=%s", ctx.skill_id)
        return SkillResult.fail(
            ctx.skill_id,
            code=codes["SKILL_INTERNAL_ERROR"],
            message=f"技能执行异常：{exc}",
            trace_id=ctx.trace_id,
        )


def _write_execution_trace(ctx: SkillInvokeContext, success: bool, error: str = "") -> None:
    """写入执行轨迹到 LlmUsageLog 和 AgentExecutionRun。"""
    try:
        from apps.skill.models import LlmUsageLog

        LlmUsageLog.objects.create(
            source_type=LlmUsageLog.SOURCE_OTHER,
            source_key=ctx.skill_id,
            project_id=ctx.project_id,
            user_id=ctx.user_id,
            success=success,
            estimated_cost_yuan=Decimal("0"),
            model_name="skill-invoker",
        )
    except Exception as exc:
        logger.debug("[SkillInvoker] 写入 LlmUsageLog 失败: %s", exc)


# ============================================================
# 技能定义加载（带缓存）
# ============================================================

_skill_def_cache: Dict[str, Any] = {}


def _load_skill_definition(skill_id: str) -> Optional[Any]:
    """加载技能定义，带进程内缓存。"""
    if skill_id in _skill_def_cache:
        return _skill_def_cache[skill_id]

    try:
        from apps.skill.models import AgentSkillDefinition
        obj = AgentSkillDefinition.objects.get(skill_id=skill_id)
        _skill_def_cache[skill_id] = obj
        return obj
    except Exception:
        return None


def clear_skill_def_cache(skill_id: Optional[str] = None) -> None:
    """清除技能定义缓存。skill_id 为空时清除全部。"""
    global _skill_def_cache
    if skill_id:
        _skill_def_cache.pop(skill_id, None)
    else:
        _skill_def_cache.clear()


# ============================================================
# SkillInvoker 主类
# ============================================================

class SkillInvoker:
    """
    统一技能调用引擎。

    用法：
        invoker = SkillInvoker()
        result = invoker.invoke(skill_id, payload, project_id, user_id)

        if result.success:
            do_something(result.data)
        else:
            handle_error(result.error)
    """

    def invoke(
        self,
        skill_id: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> SkillResult:
        """
        统一技能调用入口。

        完整流程：
        1. 加载技能定义（含缓存）
        2. 生命周期校验（draft / deprecated / gray 分流）
        3. 配额校验与预扣
        4. 入参 Schema 校验
        5. LLM 调用（支持重试 + 指数退避）
        6. 降级处理
        7. 执行轨迹写入
        8. 配额回补（如失败）
        """
        codes = _skill_error_codes()
        trace_id = str(uuid.uuid4())

        logger.info("[SkillInvoker] invoke skill=%s project=%s user=%s trace=%s",
                     skill_id, project_id, user_id, trace_id)

        # 1. 加载技能定义
        skill_def = _load_skill_definition(skill_id)
        if skill_def is None:
            logger.warning("[SkillInvoker] 技能不存在: %s", skill_id)
            return SkillResult.fail(skill_id, code=codes["SKILL_NOT_FOUND"],
                                    message=f"技能 {skill_id} 不存在", trace_id=trace_id)

        # 2. 构建上下文
        ctx = SkillInvokeContext(
            skill_id=skill_id,
            project_id=project_id,
            user_id=user_id,
            skill_definition=skill_def,
            payload=payload,
            trace_id=trace_id,
            started_at=time.time(),
        )

        # 3. 生命周期校验
        err = _check_lifecycle(ctx)
        if err:
            return err

        # 4. 配额检查与预扣
        ctx.quota_cost = float(skill_def.quota_cost or 0)
        err = _check_and_charge_quota(ctx)
        if err:
            return err

        # 5. 执行（含重试 + 降级）
        try:
            result = _execute_with_retry(ctx)
        except Exception as exc:
            logger.exception("[SkillInvoker] 未知异常 skill=%s", skill_id)
            result = SkillResult.fail(
                skill_id,
                code=codes["SKILL_INTERNAL_ERROR"],
                message=f"技能调用异常：{exc}",
                trace_id=trace_id,
            )

        # 6. 失败时回补配额
        if not result.success:
            _refund_quota(ctx)

        logger.info(
            "[SkillInvoker] result skill=%s success=%s duration=%.0fms trace=%s",
            skill_id, result.success, result.duration_ms, trace_id,
        )
        return result

    def invoke_batch(
        self,
        items: List[Dict[str, Any]],
        project_id: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> List[SkillResult]:
        """
        批量调用技能（串行，保留每个结果）。

        items: [{"skill_id": "...", "payload": {...}}, ...]
        """
        results = []
        for item in items:
            result = self.invoke(
                skill_id=item["skill_id"],
                payload=item.get("payload", {}),
                project_id=project_id,
                user_id=user_id,
            )
            results.append(result)
        return results

    def get_skill_status(self, skill_id: str) -> Dict[str, Any]:
        """查询技能当前状态（生命周期 / 调用统计）。"""
        from apps.skill.models import AgentSkillDefinition

        try:
            skill = AgentSkillDefinition.objects.get(skill_id=skill_id)
        except AgentSkillDefinition.DoesNotExist:
            return {"exists": False}

        return {
            "exists": True,
            "skill_id": skill.skill_id,
            "name": skill.name,
            "lifecycle_status": skill.lifecycle_status,
            "gray_weight": skill.gray_weight,
            "quota_cost": float(skill.quota_cost or 0),
            "timeout_seconds": skill.timeout_seconds,
            "version": skill.version,
            "published_at": skill.published_at.isoformat() if skill.published_at else None,
            "deprecated_at": skill.deprecated_at.isoformat() if skill.deprecated_at else None,
        }


# ============================================================
# 模块级单例
# ============================================================

_invoker_instance: Optional[SkillInvoker] = None


def get_skill_invoker() -> SkillInvoker:
    global _invoker_instance
    if _invoker_instance is None:
        _invoker_instance = SkillInvoker()
    return _invoker_instance
