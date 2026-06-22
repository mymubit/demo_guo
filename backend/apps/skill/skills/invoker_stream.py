# -*- coding: utf-8 -*-
"""流式技能/Agent 编排 — SSE 事件枚举与格式化。"""
from __future__ import annotations

import json
import time
import uuid
from enum import Enum
from typing import Any, Dict, Iterator, Optional


PROTOCOL_VERSION = "1.2"
WATCHDOG_SECONDS = 120
TOKEN_THROTTLE_MS = 150


class StreamEventType(str, Enum):
    START = "start"
    TOKEN = "token"
    ITEM = "item"
    DONE = "done"
    ERROR = "error"


def new_trace_id() -> str:
    return uuid.uuid4().hex


def format_sse(event_type: StreamEventType | str, data: Dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    name = event_type.value if isinstance(event_type, StreamEventType) else str(event_type)
    return f"event: {name}\ndata: {payload}\n\n"


def sse_heartbeat() -> str:
    return ": heartbeat\n\n"


class TokenThrottler:
    """150ms 节流 token 事件。"""

    def __init__(self, interval_ms: int = TOKEN_THROTTLE_MS) -> None:
        self._interval = interval_ms / 1000.0
        self._last_emit = 0.0
        self._pending: Optional[str] = None
        self._token_index = 0

    def push(self, delta: str) -> Iterator[str]:
        if not delta:
            return
        self._pending = (self._pending or "") + delta
        now = time.monotonic()
        if now - self._last_emit >= self._interval:
            yield from self._flush(now)

    def drain(self) -> Iterator[str]:
        if self._pending:
            yield from self._flush(time.monotonic())

    def _flush(self, now: float) -> Iterator[str]:
        if not self._pending:
            return
        self._token_index += 1
        data = {"delta": self._pending, "token_index": self._token_index}
        self._pending = None
        self._last_emit = now
        yield format_sse(StreamEventType.TOKEN, data)
