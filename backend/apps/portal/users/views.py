# -*- coding: utf-8 -*-
"""
用户资料相关视图

- 查看当前用户资料
- 更新当前用户资料
"""
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.serializers import UserProfileSerializer, UserUpdateSerializer, ChangePasswordSerializer
from apps.users.services import get_or_create_profile


# ============================================================
# 查看当前用户资料
# ============================================================

class UserProfileView(GenericAPIView):
    """获取当前登录用户的资料"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request, *args, **kwargs):
        profile = get_or_create_profile(request.user)
        serializer = self.get_serializer(profile)
        return Response(
            {"code": 0, "message": "ok", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 更新当前用户资料
# ============================================================

class UserUpdateView(GenericAPIView):
    """更新当前登录用户的资料

    支持部分字段更新（PATCH），字段：nickname, avatar_url, gender, bio, email
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)

        profile = get_or_create_profile(request.user)
        return Response(
            {
                "code": 0,
                "message": "更新成功",
                "data": UserProfileSerializer(profile).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        # 统一走 PATCH 语义
        return self.patch(request, *args, **kwargs)


class ChangePasswordView(GenericAPIView):
    """修改当前用户登录密码"""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response(
            {"code": 0, "message": "密码修改成功", "data": None},
            status=status.HTTP_200_OK,
        )
