"""
用户信息相关路由（资料查看 / 更新）

对应前缀：/api/users/
"""
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("me/", views.UserProfileView.as_view(), name="profile"),
    path("me/update/", views.UserUpdateView.as_view(), name="profile-update"),
]
