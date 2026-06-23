# -*- coding: utf-8 -*-
"""
我的作品模块路由

前缀 /api/works/
"""

from django.urls import path

from .works_views import (
    WorkListView,
    WorkDetailView,
    WorkShareCreateView,
    WorkStatsView,
    WorkExportView,
    WorkPolishApplyView,
)

app_name = "works"

urlpatterns = [
    # 作品列表
    path("", WorkListView.as_view(), name="work-list"),
    # 作品统计（放在详情前面，避免被 <project_id> 捕获）
    path("stats/", WorkStatsView.as_view(), name="work-stats"),
    path(
        "<str:project_id>/export/",
        WorkExportView.as_view(),
        name="work-export",
    ),
    path(
        "<str:project_id>/agents/polish/apply/",
        WorkPolishApplyView.as_view(),
        name="work-polish-apply",
    ),
    # 作品详情
    path(
        "<str:project_id>/",
        WorkDetailView.as_view(),
        name="work-detail",
    ),
    # 作品分享
    path(
        "<str:project_id>/share/",
        WorkShareCreateView.as_view(),
        name="work-share-create",
    ),
]
