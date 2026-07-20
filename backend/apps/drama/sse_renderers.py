# -*- coding: utf-8 -*-
"""SSE 响应渲染器：满足 DRF 对 Accept: text/event-stream 的内容协商。"""
from __future__ import annotations

from typing import Any

from rest_framework.renderers import BaseRenderer


class EventStreamRenderer(BaseRenderer):
    """声明 text/event-stream，避免 APIView 在协商阶段返回 HTTP 406。"""

    media_type = "text/event-stream"
    format = "event-stream"
    charset = None

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, Any] | None = None,
    ) -> bytes:
        # StreamingHttpResponse 通常直接返回，不走此处；仅作协商兜底。
        if data is None:
            return b""
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        return str(data).encode("utf-8")
