# -*- coding: utf-8 -*-
"""业务异常与全局异常处理。"""
from __future__ import annotations

from typing import Any, Optional

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import DatabaseError
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.core.responses import api_error

# 成功
SUCCESS = 0

# 通用客户端错误
VALIDATION_ERROR = 4001
UNAUTHORIZED = 401
PERMISSION_DENIED = 403
NOT_FOUND = 404

# 契约错误码（workbench/api-contract.yaml）
OPTIMISTIC_LOCK_FAILED = 40901
IDEMPOTENCY_CONFLICT = 40902
SCHEMA_VALIDATION_FAILED = 42201
WORKFLOW_GATE_BLOCKED = 42202
CONFIG_OVERLAY_FORBIDDEN = 40301
PLATFORM_POLICY_UNVERIFIED = 42203

SERVER_ERROR = 500


class BusinessException(APIException):
    """可预期的业务异常，携带契约错误码。"""

    def __init__(
        self,
        code: int,
        message: str,
        *,
        http_status: int = status.HTTP_200_OK,
        detail: Optional[Any] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        self.detail = detail or message
        super().__init__(detail=self.message)


def custom_exception_handler(exc: Exception, context: dict) -> Optional[Response]:
    """DRF 全局异常处理器。"""
    if isinstance(exc, BusinessException):
        return api_error(exc.code, exc.message, status=exc.http_status, data=exc.detail)

    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(exc, ValidationError):
            errors = _flatten_validation(response.data)
            return api_error(
                VALIDATION_ERROR,
                errors or "参数校验失败",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            view = context.get("view")
            view_name = type(view).__name__ if view is not None else ""
            # 登录/刷新失败：凭证错误；其它 401：未携带或无效 token
            if view_name in {"LoginView", "TokenObtainPairView"}:
                message = "用户名或密码错误"
            elif view_name in {"RefreshView", "TokenRefreshView"}:
                message = "登录已过期，请重新登录"
            else:
                message = "未授权，请先登录"
            return api_error(UNAUTHORIZED, message, status=status.HTTP_401_UNAUTHORIZED)
        if response.status_code == status.HTTP_403_FORBIDDEN:
            return api_error(PERMISSION_DENIED, "禁止访问", status=status.HTTP_403_FORBIDDEN)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return api_error(NOT_FOUND, "资源未找到", status=status.HTTP_404_NOT_FOUND)
        return api_error(
            int(response.status_code),
            str(exc),
            status=response.status_code,
        )

    if isinstance(exc, ObjectDoesNotExist):
        return api_error(NOT_FOUND, "资源不存在", status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, PermissionDenied):
        return api_error(
            PERMISSION_DENIED,
            str(exc) or "无权限执行此操作",
            status=status.HTTP_403_FORBIDDEN,
        )
    if isinstance(exc, DatabaseError):
        return api_error(SERVER_ERROR, "数据库操作异常", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return api_error(
        SERVER_ERROR,
        "服务器繁忙，请稍后重试",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _flatten_validation(data: Any) -> str:
    """将 DRF 校验错误展平为字符串。"""
    if isinstance(data, dict):
        parts = []
        for key, value in data.items():
            parts.append(f"{key}: {_flatten_validation(value)}")
        return "; ".join(parts)
    if isinstance(data, list):
        return "; ".join(str(item) for item in data)
    return str(data)
