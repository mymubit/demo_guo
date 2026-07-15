# -*- coding: utf-8 -*-
"""JWT 认证视图。"""
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.core.responses import api_response
from apps.users.serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """最小用户注册。"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return api_response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """当前登录用户。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return api_response(UserSerializer(request.user).data)


class LoginView(TokenObtainPairView):
    """登录获取 JWT。"""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(response.data)
        return response


class RefreshView(TokenRefreshView):
    """刷新 JWT。"""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(response.data)
        return response
