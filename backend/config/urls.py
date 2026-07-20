"""根 URL 路由。"""
from django.urls import include, path

urlpatterns = [
    # Django Admin 已禁用；运营能力走前端 /admin/* 与 /api/v1/drama/admin/*
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/drama/", include("apps.drama.urls")),
    path("", include("apps.core.urls")),
]
