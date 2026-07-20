# -*- coding: utf-8 -*-
"""LLM 调用上下文（ContextVar），供 LlmProvider 单点写日志。"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class LlmCallContext:
    project_id: str | None = None
    job_id: str | None = None
    role: str = ""
    purpose: str = "artifact_generation"
    actor: str = "system"


_llm_call_context: ContextVar[LlmCallContext | None] = ContextVar("llm_call_context", default=None)
_last_llm_log_id: ContextVar[str | None] = ContextVar("last_llm_log_id", default=None)


def get_llm_call_context() -> LlmCallContext | None:
    return _llm_call_context.get()


def get_last_llm_log_id() -> str | None:
    return _last_llm_log_id.get()


def set_last_llm_log_id(log_id: str | None) -> None:
    _last_llm_log_id.set(log_id)


@contextmanager
def llm_call_scope(
    *,
    project_id: str | None = None,
    job_id: str | None = None,
    role: str = "",
    purpose: str = "artifact_generation",
    actor: str = "system",
) -> Iterator[None]:
    token = _llm_call_context.set(
        LlmCallContext(
            project_id=project_id,
            job_id=job_id,
            role=role,
            purpose=purpose,
            actor=actor,
        )
    )
    _last_llm_log_id.set(None)
    try:
        yield
    finally:
        _llm_call_context.reset(token)
