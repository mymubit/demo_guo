"""
作品管理路由

前缀 /api/works/
"""

from django.urls import path

from .views_works import WorksListView, WorksDetailView, WorksShareView

app_name = "works"

urlpatterns = [
    # 我的作品列表（分页）
    path("", WorksListView.as_view(), name="works-list"),
    # 作品详情（只返回预渲染 HTML）
    path(
        "<str:project_id>/",
        WorksDetailView.as_view(),
        name="works-detail",
    ),
    # 为作品生成分享链接
    path(
        "<str:project_id>/share/",
        WorksShareView.as_view(),
        name="works-share",
    ),
]
