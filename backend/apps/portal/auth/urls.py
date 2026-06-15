"""
认证相关路由（登录 / 注册 / 刷新 token）

对应前缀：/api/auth/
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.portal.auth import views

app_name = "portal_auth"

urlpatterns = [
    path("register/", views.UserRegisterView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
]
