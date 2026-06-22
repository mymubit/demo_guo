# -*- coding: utf-8 -*-
"""Drama Skills URL 路由配置。"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.drama.views import (
    DramaProjectViewSet,
    DramaRoleListView,
    ModelConfigView,
    QualityRadarView,
    TokenStatsView,
    WordCountValidateView,
)

router = DefaultRouter()
router.register(r"projects", DramaProjectViewSet, basename="drama-project")

urlpatterns = [
    # 角色列表
    path("roles/", DramaRoleListView.as_view(), name="drama-roles"),

    # 字数验证
    path("validate/word-count/", WordCountValidateView.as_view(), name="drama-word-validate"),

    # Token/计费统计
    path("stats/token/", TokenStatsView.as_view(), name="drama-token-stats"),

    # 模型配置（管理员）
    path("models/config/", ModelConfigView.as_view(), name="drama-model-config"),

    # 质量雷达
    path("projects/<uuid:project_id>/quality-radar/", QualityRadarView.as_view(), name="drama-quality-radar"),

    # 项目 CRUD + 进度查询
    path("", include(router.urls)),
]
