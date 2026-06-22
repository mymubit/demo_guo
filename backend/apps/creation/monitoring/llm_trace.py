# -*- coding: utf-8 -*-
"""LLM 调用全量 I/O 轨迹（链式调试：记录完整 prompt 与响应，非摘要）。"""
from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from typing import Any, Dict, Optional

from django.conf import settings

try:
    from apps.workflow.fusion.upstream_context import summarize_upstream_for_trace
except ImportError:
    def summarize_upstream_for_trace(artifacts: dict) -> str:  # type: ignore[misc]
        """兼容存根：workflow/fusion 不可用时返回空摘要。"""
        return ""

logger = logging.getLogger(__name__)

_TRACE_CTX: ContextVar[Optional[Dict[str, Any]]] = ContextVar("llm_trace_ctx", default=None)

_DEFAULT_MAX_CHARS = 262144


def is_full_llm_trace_enabled() -> bool:
    return getattr(settings, "CREATION_LLM_TRACE_FULL", True)


def _max_chars() -> int:
    try:
        return max(4096, int(getattr(settings, "CREATION_LLM_TRACE_MAX_CHARS", _DEFAULT_MAX_CHARS) or _DEFAULT_MAX_CHARS))
    except (TypeError, ValueError):
        return _DEFAULT_MAX_CHARS


def _clip_text(text: str, *, field: str = "") -> Dict[str, Any]:
    limit = _max_chars()
    raw = str(text or "")
    if len(raw) <= limit:
        return {"text": raw, "truncated": False, "length": len(raw)}
    return {
        "text": raw[:limit],
        "truncated": True,
        "length": len(raw),
        "field": field,
    }


def _clip_json(value: Any) -> Any:
    if value is None:
        return None
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        text = str(value)
    clipped = _clip_text(text, field="json")
    if clipped.get("truncated"):
        return {"_truncated": True, "preview": clipped["text"], "length": clipped["length"]}
    if isinstance(value, (dict, list)):
        return value
    return clipped["text"]


def _upstream_trace_mode() -> str:
    mode = str(getattr(settings, "CREATION_LLM_TRACE_UPSTREAM_MODE", "summary") or "summary").lower()
    if mode in {"off", "summary", "full"}:
        return mode
    return "summary"


def _resolve_upstream_for_trace(
    upstream: Optional[Dict[str, Any]],
    extra: Optional[Dict[str, Any]] = None,
) -> Optional[Any]:
    if upstream is None:
        return None
    mode = _upstream_trace_mode()
    if mode == "off":
        return None
    if mode == "full":
        return _clip_json(upstream)
    return _clip_json(summarize_upstream_for_trace(upstream, extra=extra))


def begin_llm_trace(
    *,
    system_prompt: str,
    user_prompt: str,
    provider_id: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    json_mode: bool = True,
    upstream: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    if not is_full_llm_trace_enabled():
        return
    request: Dict[str, Any] = {
        "system_prompt": _clip_text(system_prompt, field="system_prompt"),
        "user_prompt": _clip_text(user_prompt, field="user_prompt"),
        "provider_id": provider_id,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "json_mode": json_mode,
    }
    if upstream is not None:
        traced = _resolve_upstream_for_trace(upstream, extra=extra)
        if traced is not None:
            request["upstream"] = traced
            request["upstream_mode"] = _upstream_trace_mode()
    if extra:
        request["extra"] = _clip_json(extra)
    _TRACE_CTX.set({"request": request})


def _build_request_payload() -> Dict[str, Any]:
    ctx = _TRACE_CTX.get()
    if not ctx:
        return {}
    return dict(ctx.get("request") or {})


def _latest_usage_log():
    from apps.skill.llm.usage_log import _usage_ctx
    from apps.skill.models import LlmUsageLog

    scope = _usage_ctx.get({}) or {}
    qs = LlmUsageLog.objects.all()
    run_id = scope.get("execution_run_id")
    sub_skill_id = scope.get("sub_skill_id")
    project_id = scope.get("project_id")
    if run_id:
        qs = qs.filter(execution_run_id=run_id)
    if sub_skill_id:
        qs = qs.filter(sub_skill_id=sub_skill_id)
    if project_id:
        qs = qs.filter(project_id=project_id)
    return qs.order_by("-created_at").first()


def _persist_usage_io(*, response_payload: Dict[str, Any]) -> None:
    if not is_full_llm_trace_enabled():
        return
    request_payload = _build_request_payload()
    if not request_payload and not response_payload:
        return
    log = _latest_usage_log()
    if not log:
        return
    updates: Dict[str, Any] = {}
    if request_payload:
        updates["request_payload"] = request_payload
    if response_payload:
        updates["response_payload"] = response_payload
    if updates:
        for key, val in updates.items():
            setattr(log, key, val)
        log.save(update_fields=list(updates.keys()))


def _sync_sub_skill_log(*, response_payload: Dict[str, Any], parsed_output: Any = None) -> None:
    if not is_full_llm_trace_enabled():
        return
    from apps.skill.llm.usage_log import _usage_ctx

    from .execution_run_service import AgentExecutionRunService

    scope = _usage_ctx.get({}) or {}
    sub_skill_id = str(scope.get("sub_skill_id") or "").strip()
    if not sub_skill_id:
        return
    request = _build_request_payload()
    upstream_payload = request.get("upstream")
    if isinstance(upstream_payload, dict) and upstream_payload:
        input_payload = upstream_payload
    elif upstream_payload is None and _upstream_trace_mode() == "off":
        input_payload = {
            "note": "upstream 未写入轨迹（见 user_prompt）；可设 CREATION_LLM_TRACE_UPSTREAM_MODE=summary|full",
            "traceExtra": (request.get("extra") or {}),
        }
    else:
        input_payload = {"request_keys": sorted(request.keys())}
    llm_io = {
        "request": request,
        "response": response_payload,
    }
    AgentExecutionRunService.record_sub_skill(
        sub_skill_id,
        "executed" if response_payload.get("success", True) else "failed",
        skill_type="llm",
        message=str(response_payload.get("error") or "")[:2000],
        input_payload=input_payload,
        output_payload=parsed_output if parsed_output is not None else response_payload.get("parsed"),
        llm_io=llm_io,
    )


def finish_llm_trace_success(*, raw_content: str, parsed_output: Any = None) -> None:
    if not is_full_llm_trace_enabled():
        _TRACE_CTX.set(None)
        return
    response_payload = {
        "success": True,
        "raw_content": _clip_text(raw_content, field="raw_content"),
        "parsed": _clip_json(parsed_output),
    }
    _persist_usage_io(response_payload=response_payload)
    _sync_sub_skill_log(response_payload=response_payload, parsed_output=parsed_output)
    _TRACE_CTX.set(None)


def finish_llm_trace_error(error: str, *, raw_content: str = "") -> None:
    if not is_full_llm_trace_enabled():
        _TRACE_CTX.set(None)
        return
    response_payload = {
        "success": False,
        "error": str(error or "")[:4000],
        "raw_content": _clip_text(raw_content, field="raw_content") if raw_content else None,
    }
    _persist_usage_io(response_payload=response_payload)
    _sync_sub_skill_log(response_payload=response_payload)
    _TRACE_CTX.set(None)


def merge_request_into_usage_record() -> None:
    """LlmUsageService.record 创建日志后立即写入 request_payload。"""
    if not is_full_llm_trace_enabled():
        return
    request_payload = _build_request_payload()
    if not request_payload:
        return
    log = _latest_usage_log()
    if not log:
        return
    log.request_payload = request_payload
    log.save(update_fields=["request_payload"])
