# -*- coding: utf-8 -*-
"""Runtime contract helpers for workflow execution.

This module is intentionally small and dependency-light. It gives the
orchestration layer one place to describe what entered a node, how large it
was, whether it exceeded budget, and what should be persisted as trace data.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from django.conf import settings


DEFAULT_WARN_INPUT_BYTES = 384 * 1024
DEFAULT_MAX_INPUT_BYTES = 1024 * 1024
DEFAULT_MAX_CONTEXT_BYTES = 2 * 1024 * 1024


class RuntimeBudgetExceeded(RuntimeError):
    """Raised when a node input is too large to call safely."""

    def __init__(self, message: str, *, snapshot: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.snapshot = snapshot or {}


@dataclass(frozen=True)
class RuntimeBudget:
    warn_input_bytes: int
    max_input_bytes: int
    max_context_bytes: int


def json_size_bytes(value: Any) -> Tuple[int, str]:
    """Return UTF-8 JSON byte size and serialized text."""
    text = json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)
    return len(text.encode("utf-8")), text


def estimate_tokens_from_bytes(size_bytes: int) -> int:
    """Cheap rough token estimate used only for budgeting display."""
    if size_bytes <= 0:
        return 0
    return max(1, int(size_bytes / 3))


def short_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def summarize_value(value: Any, *, max_depth: int = 2) -> Any:
    """Small structural summary that avoids storing large payload bodies."""
    if max_depth < 0:
        return {"type": type(value).__name__}
    if isinstance(value, dict):
        keys = list(value.keys())
        return {
            "type": "dict",
            "key_count": len(keys),
            "keys": [str(k) for k in keys[:24]],
            "children": {
                str(k): summarize_value(value[k], max_depth=max_depth - 1)
                for k in keys[:8]
            },
        }
    if isinstance(value, list):
        return {
            "type": "list",
            "len": len(value),
            "items": [summarize_value(v, max_depth=max_depth - 1) for v in value[:5]],
        }
    if isinstance(value, str):
        return {
            "type": "str",
            "chars": len(value),
            "preview": value[:160],
        }
    return {"type": type(value).__name__, "value": value if isinstance(value, (int, float, bool)) else str(value)[:80]}


def snapshot_payload(payload: Any) -> Dict[str, Any]:
    size, text = json_size_bytes(payload)
    keys = list(payload.keys()) if isinstance(payload, dict) else []
    return {
        "bytes": size,
        "estimated_tokens": estimate_tokens_from_bytes(size),
        "sha256_16": short_digest(text),
        "top_keys": [str(k) for k in keys[:40]],
        "key_count": len(keys),
        "shape": summarize_value(payload),
    }


def runtime_budget_for_node(node_config: Any = None) -> RuntimeBudget:
    runtime = getattr(node_config, "runtime_config", None) or {}
    return RuntimeBudget(
        warn_input_bytes=int(
            runtime.get("warn_input_bytes")
            or getattr(settings, "WORKFLOW_SKILL_INPUT_WARN_BYTES", DEFAULT_WARN_INPUT_BYTES)
        ),
        max_input_bytes=int(
            runtime.get("max_input_bytes")
            or getattr(settings, "WORKFLOW_SKILL_INPUT_MAX_BYTES", DEFAULT_MAX_INPUT_BYTES)
        ),
        max_context_bytes=int(
            runtime.get("max_context_bytes")
            or getattr(settings, "WORKFLOW_INSTANCE_CONTEXT_MAX_BYTES", DEFAULT_MAX_CONTEXT_BYTES)
        ),
    )


def enforce_input_budget(payload: Any, node_config: Any = None) -> Dict[str, Any]:
    snapshot = snapshot_payload(payload)
    budget = runtime_budget_for_node(node_config)
    snapshot["budget"] = {
        "warn_input_bytes": budget.warn_input_bytes,
        "max_input_bytes": budget.max_input_bytes,
        "warned": bool(budget.warn_input_bytes and snapshot["bytes"] > budget.warn_input_bytes),
    }
    if budget.max_input_bytes and snapshot["bytes"] > budget.max_input_bytes:
        raise RuntimeBudgetExceeded(
            (
                f"node input too large: {snapshot['bytes']} bytes "
                f"> budget {budget.max_input_bytes} bytes"
            ),
            snapshot=snapshot,
        )
    return snapshot


def project_seed_context(project: Any) -> Dict[str, Any]:
    if project is None:
        return {}
    return {
        "project_id": str(getattr(project, "id", "") or ""),
        "theme": getattr(project, "theme", "") or "",
        "core_idea": getattr(project, "core_idea", "") or "",
        "episode_count": getattr(project, "episode_count", None),
        "format_variant": getattr(project, "format_variant", "") or "",
        "audience": getattr(project, "audience", "") or "",
        "reference_work": getattr(project, "reference_work", "") or "",
        "creation_entry": getattr(project, "creation_entry", "") or "",
        "target_platform": getattr(project, "target_platform", "") or "",
    }


def node_input_snapshot(context: Dict[str, Any], node_config: Any, *, payload: Any = None) -> Dict[str, Any]:
    node_id = getattr(node_config, "node_id", "") or ""
    ctx = context or {}
    snapshot = {
        "node_id": node_id,
        "context": snapshot_payload(ctx),
    }
    if payload is not None:
        snapshot["payload"] = snapshot_payload(payload)
    return snapshot


def compress_context_for_storage(context: Dict[str, Any], node_config: Any = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Compress instance context if it exceeds the node budget."""
    budget = runtime_budget_for_node(node_config)
    size, _ = json_size_bytes(context or {})
    if not budget.max_context_bytes or size <= budget.max_context_bytes:
        return context or {}, {"level": 0, "bytes_before": size, "bytes_after": size}

    compressed: Dict[str, Any] = {
        "_compressed": True,
        "_compression_reason": "context_budget_exceeded",
        "keys": list((context or {}).keys()),
    }
    nodes = (context or {}).get("nodes")
    if isinstance(nodes, dict):
        compressed["nodes"] = {
            key: summarize_value(value, max_depth=1)
            for key, value in nodes.items()
        }
    for key in (
        "project_id",
        "theme",
        "core_idea",
        "episode_count",
        "format_variant",
        "creation_entry",
        "current_node_id",
    ):
        if key in (context or {}):
            compressed[key] = context[key]

    size_after, _ = json_size_bytes(compressed)
    return compressed, {
        "level": 1,
        "bytes_before": size,
        "bytes_after": size_after,
        "max_context_bytes": budget.max_context_bytes,
    }


def record_execution_event(
    execution: Any,
    event_type: str,
    *,
    level: str = "info",
    message: str = "",
    duration_ms: int = 0,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Legacy NodeExecutionEvent 已删除，保留 no-op 兼容调用。"""
    _ = (execution, event_type, level, message, duration_ms, extra)

