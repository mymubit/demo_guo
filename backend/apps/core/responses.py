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
    status: int = 200,
    data: Optional[Any] = None,
) -> Response:
    """返回业务错误信封。"""
    return api_response(data=data, code=code, message=message, status=status)
