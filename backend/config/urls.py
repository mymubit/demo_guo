"""
URL configuration for ScriptForge project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok", "service": "ScriptForge API"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check),
    path("api/auth/", include("apps.users.urls_auth")),
    path("api/users/", include("apps.users.urls")),
    path("api/members/", include("apps.membership.urls")),
    path("api/orders/", include("apps.orders.urls")),
    path("api/creation/", include("apps.creation.urls")),
    path("api/works/", include("apps.creation.urls_works")),
    path("api/admin/", include("apps.admin_panel.urls")),
]
