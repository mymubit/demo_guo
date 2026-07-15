"""根 URL 路由。"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/drama/", include("apps.drama.urls")),
    path("", include("apps.core.urls")),
]
