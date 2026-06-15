# -*- coding: utf-8 -*-
"""动态配置中心路由。"""
from django.urls import path

from .views import (
    AdminSystemConfigAuditLogView,
    AdminSystemConfigBulkUpdateView,
    AdminSystemConfigCategoryDetailView,
    AdminSystemConfigCategoryListCreateView,
    AdminSystemConfigDetailView,
    AdminSystemConfigListCreateView,
    AdminSystemConfigRefreshCacheView,
    AdminSystemConfigToggleView,
    PublicSystemConfigBatchView,
    PublicSystemConfigDetailView,
    PublicSystemConfigView,
)

app_name = "system_config"

admin_urlpatterns = [
    path("config-categories/", AdminSystemConfigCategoryListCreateView.as_view(), name="admin-config-categories"),
    path("config-categories/<uuid:category_id>/", AdminSystemConfigCategoryDetailView.as_view(), name="admin-config-category-detail"),
    path("configs/", AdminSystemConfigListCreateView.as_view(), name="admin-configs"),
    path("configs/bulk-update/", AdminSystemConfigBulkUpdateView.as_view(), name="admin-configs-bulk-update"),
    path("configs/refresh-cache/", AdminSystemConfigRefreshCacheView.as_view(), name="admin-configs-refresh-cache"),
    path("configs/audit-logs/", AdminSystemConfigAuditLogView.as_view(), name="admin-configs-audit-logs"),
    path("configs/<uuid:config_id>/", AdminSystemConfigDetailView.as_view(), name="admin-config-detail"),
    path("configs/<uuid:config_id>/toggle/", AdminSystemConfigToggleView.as_view(), name="admin-config-toggle"),
]

public_urlpatterns = [
    path("public/", PublicSystemConfigView.as_view(), name="public-configs"),
    path("batch/", PublicSystemConfigBatchView.as_view(), name="public-configs-batch"),
    path("<str:config_key>/", PublicSystemConfigDetailView.as_view(), name="public-config-detail"),
]
