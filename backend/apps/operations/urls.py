# -*- coding: utf-8 -*-
"""operations 路由。

  /api/admin/operations/*       - 后台（apps.console.urls 挂载 admin_urlpatterns）
  /api/operations/*            - C 端（apps.portal.urls 挂载 portal_urlpatterns）
"""
from django.urls import path

from . import portal_views, views

app_name = "operations"

# 后台路由（由 apps.console.urls 通过 include 挂载到 /api/admin/operations/）
admin_urlpatterns = [
    path("dashboard/", views.OperationsDashboardView.as_view(), name="ops-dashboard"),
    path("content-quality/", views.ContentQualityView.as_view(), name="ops-content-quality"),
    path("config-hit/", views.ConfigHitView.as_view(), name="ops-config-hit"),
    # 反馈
    path("feedback/", views.FeedbackListView.as_view(), name="ops-feedback-list"),
    path("feedback/summary/", views.FeedbackSummaryView.as_view(), name="ops-feedback-summary"),
    path("feedback/<uuid:feedback_id>/", views.FeedbackDetailView.as_view(), name="ops-feedback-detail"),
    # 抽样
    path("samples/", views.SampleListView.as_view(), name="ops-samples"),
    path("samples/mark/", views.SampleMarkView.as_view(), name="ops-samples-mark"),
    # 行为事件查询
    path("behavior/", views.BehaviorEventListView.as_view(), name="ops-behavior-list"),
]

# C 端路由（由 apps.portal.urls 通过 include 挂载到 /api/operations/）
portal_urlpatterns = [
    path("feedback/", portal_views.PortalFeedbackListView.as_view(), name="portal-feedback-list"),
    path("feedback/create/", portal_views.PortalFeedbackCreateView.as_view(), name="portal-feedback-create"),
    path("track/", portal_views.PortalTrackEventView.as_view(), name="portal-track"),
]
