"""
创作模块路由

前缀 /api/creation/
"""

from django.urls import path

from .views import (
    CreationSubmitView,
    CreationProgressView,
    CreationDownloadView,
    CreationDownloadByTokenView,
    CreationShareCreateView,
    ShareView,
)

app_name = "creation"

urlpatterns = [
    # 提交创作
    path("submit/", CreationSubmitView.as_view(), name="creation-submit"),
    # 查询进度
    path(
        "progress/<str:project_id>/",
        CreationProgressView.as_view(),
        name="creation-progress",
    ),
    # 按作品下载（登录用户）
    path(
        "download/<str:project_id>/",
        CreationDownloadView.as_view(),
        name="creation-download",
    ),
    # 一次性 token 下载（匿名 / 分享场景）
    path(
        "dl/<str:token>/",
        CreationDownloadByTokenView.as_view(),
        name="creation-download-by-token",
    ),
    # 生成分享链接
    path(
        "share/<str:project_id>/",
        CreationShareCreateView.as_view(),
        name="creation-share-create",
    ),
    # 查看分享页（公开）
    path(
        "share/view/<str:token>/",
        ShareView.as_view(),
        name="creation-share-view",
    ),
]
