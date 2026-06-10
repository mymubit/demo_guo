"""
用户资料路由
"""
from django.urls import path
from .views import ProfileView

urlpatterns = [
    path("me/", ProfileView.as_view(), name="user-profile"),
]
