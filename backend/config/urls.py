"""
URL configuration for ScriptForge project.

路由分层：
  /api/          -> apps.portal（前台用户 API）
  /api/admin/    -> apps.console（后台管理 API）
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_check(request):
    return JsonResponse({"status": "ok", "service": "ScriptForge API"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/monitoring/", include("apps.monitoring.urls")),
    path("api/", include("apps.portal.urls")),
    path("api/admin/", include("apps.console.urls")),
    path("dj_queue/", include("dj_queue.urls")),
]
