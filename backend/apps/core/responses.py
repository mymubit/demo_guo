# -*- coding: utf-8 -*-
"""统一 API 响应封装。"""
from __future__ import annotations

from typing import Any, Optional

from rest_framework.response import Response


def api_response(
    data: Any = None,
    *,
    code: int = 0,
    message: str = "ok",
    status: int = 200,
) -> Response:
    """返回 {code, message, data} 信封。"""
    return Response({"code": code, "message": message, "data": data}, status=status)


def api_error(
    code: int,
    message: str,
    *,
    status: Optional[int] = None,
    data: Optional[Any] = None,
) -> Response:
    """返回业务错误信封。

    HTTP status 默认与常见业务码对齐（401/403/404/500），其余默认 400，
    避免「业务失败却 HTTP 200」导致客户端与监控误判。
    """
    if status is None:
        if code in (401, 403, 404, 500):
            status = code
        elif code >= 500:
            status = 500
        else:
            status = 400
    return api_response(data=data, code=code, message=message, status=status)
