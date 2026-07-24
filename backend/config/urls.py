"""根 URL 路由。"""
from django.urls import include, path

from apps.drama.api.v2_gone import V2GoneView

urlpatterns = [
    # Django Admin 已禁用；产品 API 为 /api/v3/；旧 /api/v2 统一 410。
    path("api/v1/", include("apps.users.urls")),
    path("api/v2/", V2GoneView.as_view()),
    path("api/v2/<path:rest>", V2GoneView.as_view()),
    path("api/v3/", include("apps.drama.api.v3.urls")),
    path("", include("apps.core.urls")),
]
