"""
安全中间件集合

- RequestSignatureMiddleware: 请求签名验证中间件
- RateLimitMiddleware: 接口限流中间件
- AuditLogMiddleware: 审计日志中间件

中间件顺序（建议在 settings.MIDDLEWARE 中）:
    1. RequestSignatureMiddleware （最外层，签名验证不通过直接返回）
    2. RateLimitMiddleware         （通过签名后判断限流）
    3. AuditLogMiddleware          （最内层，包裹业务处理，记录响应状态）
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .models import AuditLog
from .services import (
    RateLimitService,
    SignatureService,
    get_rate_limit,
    get_signature,
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# 路径匹配工具
# ----------------------------------------------------------------------
# 不需要签名验证 / 限流 / 审计的路径白名单（使用前缀匹配）
DEFAULT_SKIP_PATHS: tuple[str, ...] = (
    "/admin/",
    "/static/",
    "/media/",
    "/health/",
    "/favicon.ico",
    "/robots.txt",
)

# 必须签名验证的路径（不匹配则直接拒绝），None 表示所有非白名单路径都需要
REQUIRE_SIGNATURE_PATHS: tuple[str, ...] | None = None


def _path_should_check(path: str, skip_paths: tuple[str, ...]) -> bool:
    """
    判断路径是否需要经过安全检查。
    """
    if not path:
        return False
    for prefix in skip_paths:
        if path.startswith(prefix):
            return False
    return True


def _get_client_ip(request: HttpRequest) -> str | None:
    """
    从请求中提取客户端 IP。
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
        if ip:
            return ip
    return request.META.get("REMOTE_ADDR") or None


# ======================================================================
# 请求签名验证中间件
# ======================================================================
class RequestSignatureMiddleware(MiddlewareMixin):
    """
    请求签名验证中间件

    检查 HTTP 请求头：
        X-Timestamp         Unix 时间戳（秒）
        X-Nonce             一次性随机字符串
        X-Signature         HMAC-SHA256 签名（小写 hex）
        X-Device-Fingerprint 可选的设备指纹

    算法：
        signature = hex( HMAC-SHA256(secret, method + path + timestamp + nonce + body_hash) )

    防重放：
        - 时间窗口内（默认 5 分钟）的请求有效
        - Nonce 在时间窗口内不能重复使用（Redis 存储）
    """

    # 可通过 settings 覆盖：SECURITY_SIGNATURE_SKIP_PATHS
    skip_paths_attr = "SECURITY_SIGNATURE_SKIP_PATHS"
    enable_attr = "SECURITY_SIGNATURE_ENABLED"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        super().__init__(get_response)
        self.get_response = get_response
        self._signature: SignatureService = get_signature()
        from django.conf import settings

        self._skip_paths: tuple[str, ...] = tuple(
            getattr(settings, self.skip_paths_attr, DEFAULT_SKIP_PATHS)
        )
        self._enabled: bool = bool(getattr(settings, self.enable_attr, True))
        # 如配置了 REQUIRE_SIGNATURE_PATHS，仅对这些路径强制签名
        self._require_paths: tuple[str, ...] | None = getattr(
            settings, "SECURITY_SIGNATURE_REQUIRE_PATHS", REQUIRE_SIGNATURE_PATHS
        )

    # ---- Django 3.2+ 风格的 __call__ ----
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # 白名单路径 / 关闭开关 直接跳过
        if not self._enabled or not _path_should_check(request.path, self._skip_paths):
            return self.get_response(request)

        # 若配置了强制签名路径，未命中则跳过
        if self._require_paths is not None:
            hit = any(request.path.startswith(p) for p in self._require_paths)
            if not hit:
                return self.get_response(request)

        result = self._verify(request)
        if not result:
            # 签名不通过，记录审计日志并返回 401
            try:
                body_preview = self._get_body_hash(request)
            except Exception:
                body_preview = None
            AuditLog.log(
                action=AuditLog.ActionType.SIGNATURE_FAIL,
                request=request,
                extra_info={
                    "reason": result.reason,
                    "signature": result.signature[:32] + "..." if result.signature else "",
                    "ts": result.ts,
                    "nonce": result.nonce,
                },
                request_hash=body_preview,
            )
            return JsonResponse(
                {
                    "code": 40101,
                    "message": f"请求签名验证失败: {result.reason}",
                    "detail": result.reason,
                },
                status=401,
            )

        # 把 nonce / ts 放到 request 上，供下游使用
        request._security_signature_nonce = result.nonce
        request._security_signature_ts = result.ts

        return self.get_response(request)

    # ---- 核心验证 ----
    def _verify(self, request: HttpRequest) -> "SignatureService._":  # 实际返回 SignatureResult
        ts = request.META.get("HTTP_X_TIMESTAMP")
        nonce = request.META.get("HTTP_X_NONCE")
        signature = request.META.get("HTTP_X_SIGNATURE")

        # body_hash：优先使用头里的 X-Body-Hash（客户端提供），
        # 否则在服务端计算请求体 hash
        body_hash = request.META.get("HTTP_X_BODY_HASH")
        if not body_hash:
            try:
                body_hash = self._get_body_hash(request)
            except Exception as exc:
                logger.exception("请求体哈希失败: %s", exc)
                body_hash = ""

        return self._signature.verify(
            method=request.method,
            path=request.path,
            timestamp=ts,
            nonce=nonce,
            body_hash=body_hash,
            signature=signature,
        )

    def _get_body_hash(self, request: HttpRequest) -> str:
        """
        计算请求体 SHA-256。

        注意：Django 的 request.body 在中间件中访问是安全的，但一旦被视图读取，
        视图就只能通过已读取的副本访问。此处提前读取 body 并缓存结果。
        """
        cached = getattr(request, "_security_body_hash", None)
        if cached is not None:
            return cached

        body = request.body or b""
        body_hash = hashlib.sha256(body).hexdigest()
        request._security_body_hash = body_hash  # type: ignore[attr-defined]
        return body_hash


# ======================================================================
# 接口限流中间件
# ======================================================================
class RateLimitMiddleware(MiddlewareMixin):
    """
    基于用户ID + IP 的接口限流中间件

    使用 RateLimitService 维护固定窗口计数器，超出限制返回 429 Too Many Requests。
    响应头会附加：
        X-RateLimit-Limit       当前窗口最大请求数
        X-RateLimit-Remaining   剩余可用请求数
        X-RateLimit-Reset       窗口重置剩余秒数
    """

    skip_paths_attr = "SECURITY_RATE_LIMIT_SKIP_PATHS"
    enable_attr = "SECURITY_RATE_LIMIT_ENABLED"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        super().__init__(get_response)
        self.get_response = get_response
        self._rate_limit: RateLimitService = get_rate_limit()
        from django.conf import settings

        self._skip_paths: tuple[str, ...] = tuple(
            getattr(settings, self.skip_paths_attr, DEFAULT_SKIP_PATHS)
        )
        self._enabled: bool = bool(getattr(settings, self.enable_attr, True))

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self._enabled or not _path_should_check(request.path, self._skip_paths):
            return self.get_response(request)

        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = request.user.id

        ip = _get_client_ip(request) or "unknown"

        result = self._rate_limit.check(user_id=user_id, ip=ip, path=request.path)

        # 无论是否通过，都把限流信息写入响应头
        if not result.allowed:
            AuditLog.log(
                action=AuditLog.ActionType.RATE_LIMIT,
                request=request,
                extra_info={
                    "limit": result.limit,
                    "window": result.window,
                    "remaining": result.remaining,
                    "reset_after": result.reset_after,
                    "key": result.key,
                },
            )
            response = JsonResponse(
                {
                    "code": 42901,
                    "message": "请求过于频繁，请稍后再试",
                    "detail": {
                        "limit": result.limit,
                        "window": result.window,
                        "reset_after": result.reset_after,
                    },
                },
                status=429,
            )
        else:
            response = self.get_response(request)

        # 附加限流头
        response["X-RateLimit-Limit"] = str(result.limit)
        response["X-RateLimit-Remaining"] = str(result.remaining)
        response["X-RateLimit-Reset"] = str(result.reset_after)

        return response


# ======================================================================
# 审计日志中间件
# ======================================================================
class AuditLogMiddleware(MiddlewareMixin):
    """
    审计日志中间件

    包裹整个请求处理流程，记录所有命中的请求信息。默认对所有非静态/非管理请求
    记录一条 API_CALL 审计日志，可结合 AuditLog.log() 在业务中自定义 action。
    """

    skip_paths_attr = "SECURITY_AUDIT_SKIP_PATHS"
    enable_attr = "SECURITY_AUDIT_ENABLED"

    # 需要提升为更敏感 action 的 HTTP 方法
    SENSITIVE_METHODS: tuple[str, ...] = ("POST", "PUT", "PATCH", "DELETE")

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        super().__init__(get_response)
        self.get_response = get_response
        from django.conf import settings

        self._skip_paths: tuple[str, ...] = tuple(
            getattr(settings, self.skip_paths_attr, DEFAULT_SKIP_PATHS)
        )
        self._enabled: bool = bool(getattr(settings, self.enable_attr, True))
        # 敏感路径 -> action 映射
        self._path_action: dict[str, str] = getattr(
            settings, "SECURITY_AUDIT_PATH_ACTIONS", {}
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self._enabled or not _path_should_check(request.path, self._skip_paths):
            return self.get_response(request)

        # 预计算 body_hash（如果尚未计算）
        try:
            body_hash = hashlib.sha256(request.body or b"").hexdigest()
        except Exception:
            body_hash = None

        # 捕获可能的异常，确保无论成功失败都记录日志
        try:
            response = self.get_response(request)
        except Exception as exc:
            # 记录异常请求后重新抛出，交由外层异常处理
            try:
                self._record(request, None, body_hash, exc)
            except Exception:
                logger.exception("审计日志写入失败")
            raise

        # 正常响应记录
        try:
            self._record(request, response, body_hash, None)
        except Exception:
            logger.exception("审计日志写入失败")

        return response

    # ---- 记录 ----
    def _record(
        self,
        request: HttpRequest,
        response: HttpResponse | None,
        body_hash: str | None,
        exc: Exception | None,
    ) -> None:
        action = self._resolve_action(request, response, exc)

        # 补充信息
        extra = {
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:200],
            "referer": request.META.get("HTTP_REFERER", "")[:200],
            "content_length": int(request.META.get("CONTENT_LENGTH") or 0),
        }
        if exc is not None:
            extra["exception"] = f"{type(exc).__name__}: {str(exc)[:200]}"

        # 响应体大小
        if response is not None:
            try:
                extra["response_size"] = len(response.content)
            except Exception:
                pass

        AuditLog.log(
            action=action,
            request=request,
            response=response,
            request_hash=body_hash,
            extra_info=extra,
        )

    def _resolve_action(
        self,
        request: HttpRequest,
        response: HttpResponse | None,
        exc: Exception | None,
    ) -> str:
        """
        根据请求路径/方法/响应状态推断 action。
        """
        # 1. 手动映射优先
        for prefix, act in self._path_action.items():
            if request.path.startswith(prefix):
                return act

        # 2. 状态码判断
        if response is not None:
            status = response.status_code
            if status in (401, 403):
                return AuditLog.ActionType.PERMISSION_DENY
        if exc is not None:
            return AuditLog.ActionType.OTHER

        # 3. 方法判断
        method = (request.method or "").upper()
        if method == "POST" and ("/login" in request.path or "/signin" in request.path):
            return AuditLog.ActionType.LOGIN
        if method in ("DELETE", "PUT", "PATCH"):
            if method == "DELETE":
                return AuditLog.ActionType.DELETE
            return AuditLog.ActionType.UPDATE
        if method == "POST":
            return AuditLog.ActionType.CREATE
        if method == "GET":
            return AuditLog.ActionType.READ

        return AuditLog.ActionType.API_CALL
