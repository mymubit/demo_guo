# -*- coding: utf-8 -*-
"""Drama Skills URL 路由配置"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.drama.views import (
    DramaWorkspaceViewSet,
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
router.register(r"projects", DramaWorkspaceViewSet, basename="drama-project")

urlpatterns = [
    # 角色分组列表
    path("roles/", DramaRoleListView.as_view(), name="drama-roles"),

    # 字数校验
    path("validate/word-count/", WordCountValidateView.as_view(), name="drama-word-validate"),

    # Token/统计
    path("stats/token/", TokenStatsView.as_view(), name="drama-token-stats"),

    # 模型配置管理（管理员）
    path("models/config/", ModelConfigView.as_view(), name="drama-model-config"),

    # 8维度质量雷达图（支持单集/全剧）
    path("projects/<uuid:project_id>/quality-radar/", QualityRadarView.as_view(), name="drama-quality-radar"),

    # 单集质量报告（GET=列表 POST=提交）
    path("projects/<uuid:project_id>/episode-quality/", EpisodeQualityView.as_view(), name="drama-episode-quality"),

    # 单集剧本内容获取 + 修改建议应用
    path("projects/<uuid:project_id>/episodes/", EpisodeArtifactView.as_view(), name="drama-episodes"),

    # 批量生成计划（100集模式，token成本预估）
    path("projects/<uuid:project_id>/generation-plan/", GenerationPlanView.as_view(), name="drama-generation-plan"),

    # 工作区 CRUD + 进度查询 + 角色执行
    path("", include(router.urls)),
]
