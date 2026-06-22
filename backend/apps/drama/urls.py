# -*- coding: utf-8 -*-
"""Drama Skills URL 路由配置。"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.drama.views import (
    DramaProjectViewSet,
    DramaRoleListView,
    EpisodeArtifactView,
    EpisodeQualityView,
    GenerationPlanView,
    ModelConfigView,
    QualityRadarView,
    TokenStatsView,
    WordCountValidateView,
)

router = DefaultRouter()
router.register(r"projects", DramaProjectViewSet, basename="drama-project")

urlpatterns = [
    # 角色列表（含三层分级）
    path("roles/", DramaRoleListView.as_view(), name="drama-roles"),

    # 字数验证
    path("validate/word-count/", WordCountValidateView.as_view(), name="drama-word-validate"),

    # Token/计费统计
    path("stats/token/", TokenStatsView.as_view(), name="drama-token-stats"),

    # 模型配置（管理员）
    path("models/config/", ModelConfigView.as_view(), name="drama-model-config"),

    # 质量雷达（整剧或分集，含扣分点详情）
    path("projects/<uuid:project_id>/quality-radar/", QualityRadarView.as_view(), name="drama-quality-radar"),

    # 分集质量评估（GET=列表，POST=提交单集评估）
    path("projects/<uuid:project_id>/episode-quality/", EpisodeQualityView.as_view(), name="drama-episode-quality"),

    # 分集产物管理（剧本内容读写 + 建议应用）
    path("projects/<uuid:project_id>/episodes/", EpisodeArtifactView.as_view(), name="drama-episodes"),

    # 分集生成计划（解决100集token爆炸问题）
    path("projects/<uuid:project_id>/generation-plan/", GenerationPlanView.as_view(), name="drama-generation-plan"),

    # 项目 CRUD + 进度查询 + 角色执行
    path("", include(router.urls)),
]
