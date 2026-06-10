# apps/common/exceptions.py
# 自定义异常及全局异常处理器

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import DatabaseError

# ============================================================
# 常用错误码常量
# ============================================================
SUCCESS = 0              # 成功
PARAM_ERROR = 400        # 参数错误
UNAUTHORIZED = 401       # 未授权
FORBIDDEN = 403          # 禁止访问
NOT_FOUND = 404          # 资源未找到
SERVER_ERROR = 500       # 服务器内部错误


# ============================================================
# 自定义业务异常类
# ============================================================
class BusinessException(APIException):
    """业务异常类。

    用于在业务逻辑中主动抛出异常，携带自定义的 code 和 message 信息。
    """

    status_code = status.HTTP_200_OK  # HTTP 状态码统一返回 200，业务状态码由 code 标识
    default_detail = '业务处理异常'
    default_code = SERVER_ERROR

    def __init__(self, code=None, message=None, detail=None):
        """
        :param code: 业务错误码，默认使用 SERVER_ERROR
        :param message: 面向用户的错误提示信息
        :param detail: 面向开发者的详细错误信息（可选）
        """
        self.code = code if code is not None else self.default_code
        self.message = message if message is not None else self.default_detail
        self.detail = detail if detail is not None else self.message
        super().__init__(detail=self.message, code=str(self.code))


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

    # 处理业务异常 BusinessException
    if isinstance(exc, BusinessException):
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
            exc_code = getattr(exc, 'status_code', SERVER_ERROR)
            # 对常见异常类型进行友好化处理
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                message = '参数校验失败'
                # 将 DRF 返回的字段错误信息拼接到 message 中
                errors = []
                for key, value in response.data.items():
                    if isinstance(value, list):
                        errors.append(f"{key}: {'; '.join([str(v) for v in value])}")
                    else:
                        errors.append(f"{key}: {value}")
                if errors:
                    message = '; '.join(errors)
                return Response(
                    {'code': PARAM_ERROR, 'message': message, 'data': None},
                    status=status.HTTP_200_OK,
                )
            elif response.status_code == status.HTTP_401_UNAUTHORIZED:
                return Response(
                    {'code': UNAUTHORIZED, 'message': '未授权，请先登录', 'data': None},
                    status=status.HTTP_200_OK,
                )
            elif response.status_code == status.HTTP_403_FORBIDDEN:
                return Response(
                    {'code': FORBIDDEN, 'message': '禁止访问', 'data': None},
                    status=status.HTTP_200_OK,
                )
            elif response.status_code == status.HTTP_404_NOT_FOUND:
                return Response(
                    {'code': NOT_FOUND, 'message': '资源未找到', 'data': None},
                    status=status.HTTP_200_OK,
                )
            # 其它未明确分类的 APIException
            return Response(
                {
                    'code': exc_code,
                    'message': str(exc.detail) if hasattr(exc, 'detail') else '请求异常',
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
            {'code': FORBIDDEN, 'message': '无权限执行此操作', 'data': None},
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
        {'code': SERVER_ERROR, 'message': f'服务器内部错误: {str(exc)}', 'data': None},
        status=status.HTTP_200_OK,
    )
