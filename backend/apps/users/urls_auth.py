"""
认证相关路由（登录 / 注册 / 刷新 token）

对应前缀：/api/auth/
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views_auth

app_name = "users_auth"

urlpatterns = [
    path("register/", views_auth.UserRegisterView.as_view(), name="register"),
    path("login/", views_auth.UserLoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("logout/", views_auth.UserLogoutView.as_view(), name="logout"),
]
