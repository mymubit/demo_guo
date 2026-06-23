# -*- coding: utf-8 -*-
# apps/common/exceptions.py
# 自定义异常及全局异常处理器

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import DatabaseError

from apps.common.user_messages import humanize_user_message

# ============================================================
# 业务错误码常量
# ============================================================
SUCCESS = 0               # 成功

# 4xxx — 客户端错误
VALIDATION_ERROR = 4001   # 参数校验失败（DRF ValidationError）
PARAM_MISSING = 4002      # 必填参数缺失
BUSINESS_CONFLICT = 4003  # 业务冲突（如重复操作）

# 向后兼容别名
PARAM_ERROR = VALIDATION_ERROR

# 401x — 鉴权失败
UNAUTHORIZED = 401        # 未登录 / Token 缺失
TOKEN_EXPIRED = 4011      # Token 已过期
PERMISSION_DENIED = 403   # 权限不足

# 向后兼容别名
FORBIDDEN = 403

# 通用 HTTP 映射
NOT_FOUND = 404           # 资源未找到
SERVER_ERROR = 500        # 服务器内部错误


# ============================================================
# 技能引擎错误码（7xxx）
# ============================================================
# 技能不存在 / 不可用
SKILL_NOT_FOUND        = 7001  # 技能不存在
SKILL_DISABLED         = 7002  # 技能已禁用或已废弃
SKILL_LIFECYCLE_ERROR  = 7003  # 技能生命周期状态不允许调用（如 draft）

# 技能调用异常
SKILL_VALIDATION_ERROR = 7010  # 技能入参不符合 input_schema
SKILL_TIMEOUT          = 7011  # 技能执行超时
SKILL_RATE_LIMIT       = 7012  # LLM 请求频率超限
SKILL_PROVIDER_ERROR   = 7013  # LLM Provider 返回错误
SKILL_INTERNAL_ERROR   = 7014  # 技能内部执行异常

# 配额与降级
SKILL_QUOTA_EXCEEDED   = 7020  # 用户配额不足
SKILL_FALLBACK_FAILED  = 7021  # 降级技能调用失败
SKILL_CIRCUIT_BREAK    = 7022  # 技能熔断（Tier4 P0 红线触发）


# ============================================================
# 工作流编排错误码（8xxx）
# ============================================================
# 工作流不存在 / 不可用
PIPELINE_NOT_FOUND      = 8001  # 工作流包不存在
PIPELINE_DISABLED       = 8002  # 工作流已禁用或已归档
PIPELINE_NODE_NOT_FOUND = 8010  # 工作流节点不存在
PIPELINE_CIRCULAR_DEP   = 8011  # 工作流存在循环依赖
PIPELINE_TIMEOUT        = 8012  # 节点执行超时

# 执行状态
PIPELINE_RUNNING        = 8020  # 工作流正在执行中
PIPELINE_NODE_FAILED    = 8021  # 节点执行失败
PIPELINE_ABORTED        = 8022  # 工作流被中止
PIPELINE_CONDITION_MISMATCH = 8023  # 条件分支不匹配


# ============================================================
# 配额与计费错误码（9xxx）
# ============================================================
QUOTA_EXCEEDED          = 9001  # 用户配额不足
QUOTA_PRECHARGE_FAILED  = 9010  # 预扣配额失败
QUOTA_REFUND_FAILED     = 9011  # 配额回补失败
QUOTA_INSUFFICIENT      = 9012  # 账户余额不足


# ============================================================
# 错误码 → 用户可读消息映射（可由 system_config 覆盖）
# ============================================================
ERROR_MESSAGE_MAP = {
    SUCCESS: "操作成功",
    VALIDATION_ERROR: "参数校验失败",
    PARAM_MISSING: "缺少必填参数",
    BUSINESS_CONFLICT: "业务冲突，请勿重复操作",
    UNAUTHORIZED: "未登录，请先登录",
    TOKEN_EXPIRED: "登录已过期，请重新登录",
    PERMISSION_DENIED: "权限不足，无法执行此操作",
    NOT_FOUND: "资源不存在",
    SERVER_ERROR: "服务器繁忙，请稍后重试",
    # 技能引擎
    SKILL_NOT_FOUND: "技能不存在",
    SKILL_DISABLED: "技能已下线，请联系管理员",
    SKILL_LIFECYCLE_ERROR: "技能尚未发布，暂不可用",
    SKILL_VALIDATION_ERROR: "技能输入参数不合法",
    SKILL_TIMEOUT: "技能执行超时，请稍后重试",
    SKILL_RATE_LIMIT: "请求过于频繁，请稍后重试",
    SKILL_PROVIDER_ERROR: "AI 模型服务异常，请稍后重试",
    SKILL_INTERNAL_ERROR: "技能执行异常，请联系管理员",
    SKILL_QUOTA_EXCEEDED: "配额不足，请充值后重试",
    SKILL_FALLBACK_FAILED: "服务降级失败，请稍后重试",
    SKILL_CIRCUIT_BREAK: "内容触发合规红线，创作已停止",
    # 工作流编排
    PIPELINE_NOT_FOUND: "工作流不存在",
    PIPELINE_DISABLED: "工作流已下线，请联系管理员",
    PIPELINE_NODE_NOT_FOUND: "工作流节点不存在",
    PIPELINE_CIRCULAR_DEP: "工作流存在循环依赖，请联系管理员",
    PIPELINE_TIMEOUT: "节点执行超时",
    PIPELINE_RUNNING: "工作流正在执行中",
    PIPELINE_NODE_FAILED: "节点执行失败",
    PIPELINE_ABORTED: "工作流已手动中止",
    PIPELINE_CONDITION_MISMATCH: "条件分支判断失败",
    # 配额与计费
    QUOTA_EXCEEDED: "配额不足，请充值后重试",
    QUOTA_PRECHARGE_FAILED: "配额预扣失败",
    QUOTA_REFUND_FAILED: "配额回补失败",
    QUOTA_INSUFFICIENT: "账户余额不足",
}


# ============================================================
# 自定义业务异常类
# ============================================================
class BusinessException(APIException):
    """业务异常类。

    用于在业务逻辑中主动抛出异常，携带自定义的 code 和 message 信息。
    支持：
    - 传入 code，从 ERROR_MESSAGE_MAP 自动取用户可读消息
    - 传入 message 覆盖默认消息
    - 传入 detail 给开发者看的详细上下文
    """

    status_code = status.HTTP_200_OK  # HTTP 状态码统一返回 200，业务状态码由 code 标识
    default_detail = '业务处理异常'
    default_code = SERVER_ERROR

    def __init__(self, code=None, message=None, detail=None):
        """
        :param code: 业务错误码，默认使用 SERVER_ERROR。
                      若 code 在 ERROR_MESSAGE_MAP 中且未传 message，则自动取映射值。
        :param message: 面向用户的错误提示信息
        :param detail: 面向开发者的详细错误信息（可选）
        """
        self.code = code if code is not None else self.default_code
        # 自动从错误码映射表取用户可读消息，message 参数可覆盖
        self.message = (
            message
            if message is not None
            else ERROR_MESSAGE_MAP.get(self.code, self.default_detail)
        )
        self.detail = detail if detail is not None else self.message
        super().__init__(detail=self.message, code=str(self.code))


# ============================================================
# 专用业务异常类（语法糖，减少手写 code 常量）
# ============================================================
class SkillException(BusinessException):
    """技能引擎专用异常。"""

    def __init__(self, code, message=None, detail=None):
        if message is None:
            message = ERROR_MESSAGE_MAP.get(code)
        super().__init__(code=code, message=message, detail=detail)


class PipelineException(BusinessException):
    """工作流编排专用异常。"""

    def __init__(self, code, message=None, detail=None):
        if message is None:
            message = ERROR_MESSAGE_MAP.get(code)
        super().__init__(code=code, message=message, detail=detail)


class QuotaException(BusinessException):
    """配额与计费专用异常。"""

    def __init__(self, code, message=None, detail=None):
        if message is None:
            message = ERROR_MESSAGE_MAP.get(code)
        super().__init__(code=code, message=message, detail=detail)


# ============================================================
# 全局异常处理器
# ============================================================
def custom_exception_handler(exc, context):
    """
    全局异常处理器，统一异常响应格式。

    响应格式统一为：
        {
            "code": <int>,
            "message": <str>,
            "data": null
        }
    """
    # 首先调用 DRF 默认的 exception_handler 获取标准响应
    response = exception_handler(exc, context)
    request = context.get("request")
    if request is not None:
        request._monitoring_exception = exc

    # 处理业务异常 BusinessException
    if isinstance(exc, BusinessException):
        # 若 BusinessException 传入了 code 但未传 message，
        # message 已在构造时自动取自 ERROR_MESSAGE_MAP
        return Response(
            {
                'code': exc.code,
                'message': exc.message,
                'data': None,
            },
            status=status.HTTP_200_OK,
        )

    # 处理 DRF 产生的异常（如 ValidationError、NotFound、PermissionDenied 等）
    if response is not None:
        # 根据异常类型映射错误码和消息
        if isinstance(exc, APIException):
            # 对常见异常类型进行友好化处理
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                # DRF ValidationError → 4001，拼接字段级错误信息
                errors = []
                if isinstance(response.data, dict):
                    for key, value in response.data.items():
                        if isinstance(value, list):
                            errors.append(f"{key}: {'; '.join([str(v) for v in value])}")
                        else:
                            errors.append(f"{key}: {value}")
                elif isinstance(response.data, list):
                    errors = [str(v) for v in response.data]
                message = '; '.join(errors) if errors else '参数校验失败'
                return Response(
                    {'code': VALIDATION_ERROR, 'message': message, 'data': None},
                    status=status.HTTP_200_OK,
                )
            elif response.status_code == status.HTTP_401_UNAUTHORIZED:
                return Response(
                    {'code': UNAUTHORIZED, 'message': '未授权，请先登录', 'data': None},
                    status=status.HTTP_200_OK,
                )
            elif response.status_code == status.HTTP_403_FORBIDDEN:
                return Response(
                    {'code': PERMISSION_DENIED, 'message': '禁止访问', 'data': None},
                    status=status.HTTP_200_OK,
                )
            elif response.status_code == status.HTTP_404_NOT_FOUND:
                return Response(
                    {'code': NOT_FOUND, 'message': '资源未找到', 'data': None},
                    status=status.HTTP_200_OK,
                )
            # 其它未明确分类的 APIException
            exc_code = getattr(exc, 'status_code', SERVER_ERROR)
            detail = str(exc.detail) if hasattr(exc, 'detail') else ''
            return Response(
                {
                    'code': exc_code,
                    'message': humanize_user_message(detail, default='请求异常'),
                    'data': None,
                },
                status=status.HTTP_200_OK,
            )

    # 处理 Django 内置的 ObjectDoesNotExist 异常
    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {'code': NOT_FOUND, 'message': '资源不存在', 'data': None},
            status=status.HTTP_200_OK,
        )

    # 处理 Django 内置的 PermissionDenied 异常
    if isinstance(exc, PermissionDenied):
        return Response(
            {
                'code': FORBIDDEN,
                'message': humanize_user_message(str(exc), default='无权限执行此操作'),
                'data': None,
            },
            status=status.HTTP_200_OK,
        )

    # 处理数据库异常
    if isinstance(exc, DatabaseError):
        return Response(
            {'code': SERVER_ERROR, 'message': '数据库操作异常', 'data': None},
            status=status.HTTP_200_OK,
        )

    # 处理其余所有未捕获异常，作为服务器内部错误
    return Response(
        {
            'code': SERVER_ERROR,
            'message': humanize_user_message(str(exc), default='服务器繁忙，请稍后重试'),
            'data': None,
        },
        status=status.HTTP_200_OK,
    )
