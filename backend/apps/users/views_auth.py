"""
认证相关视图

- 注册（手机号 + 密码）
- 登录（手机号 + 密码）
- 登出（可选，配合 simplejwt 黑名单）
"""
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserLoginSerializer, UserRegisterSerializer


# ============================================================
# 辅助方法
# ============================================================

def _build_token_response(user: User) -> dict:
    """构造 JWT 响应体

    返回 access / refresh / 用户基本信息
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": {
            "id": str(user.id),
            "nickname": user.nickname or "",
            "avatar_url": user.avatar_url or "",
        },
    }


# ============================================================
# 注册
# ============================================================

class UserRegisterView(CreateAPIView):
    """用户注册

    输入：phone, password, password_confirm, nickname?
    输出：JWT token 对 + 基本信息
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "code": 0,
                "message": "注册成功",
                "data": _build_token_response(user),
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


# ============================================================
# 登录
# ============================================================

class UserLoginView(GenericAPIView):
    """用户登录

    输入：phone, password
    输出：JWT token 对 + 基本信息
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(
            {
                "code": 0,
                "message": "登录成功",
                "data": _build_token_response(user),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# 登出（将 refresh 加入黑名单）
# ============================================================

class UserLogoutView(GenericAPIView):
    """用户登出

    输入：refresh token（请求体中）
    将其加入 simplejwt 黑名单，需开启 BLACKLIST_AFTER_ROTATION=True
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh") or ""
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                # 忽略已失效 token 的黑名单错误
                pass
        return Response(
            {"code": 0, "message": "已退出登录", "data": None},
            status=status.HTTP_200_OK,
        )
