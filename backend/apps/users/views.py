"""
用户资料相关视图

- 查看当前用户资料
- 更新当前用户资料
"""
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserProfile
from .serializers import UserProfileSerializer, UserUpdateSerializer


# ============================================================
# 查看当前用户资料
# ============================================================

class UserProfileView(GenericAPIView):
    """获取当前登录用户的资料"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        profile, _created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                "nickname": self.request.user.nickname or f"用户{self.request.user.id.hex[:8]}",
                "avatar_url": self.request.user.avatar_url or "",
            },
        )
        return profile

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
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

        # 返回更新后的完整资料
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "nickname": request.user.nickname,
                "avatar_url": request.user.avatar_url or "",
            },
        )
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
