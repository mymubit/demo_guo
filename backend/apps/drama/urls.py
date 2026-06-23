# -*- coding: utf-8 -*-
"""Drama Skills URL ?????"""
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
    # ???????????
    path("roles/", DramaRoleListView.as_view(), name="drama-roles"),

    # ????
    path("validate/word-count/", WordCountValidateView.as_view(), name="drama-word-validate"),

    # Token/????
    path("stats/token/", TokenStatsView.as_view(), name="drama-token-stats"),

    # ?????????
    path("models/config/", ModelConfigView.as_view(), name="drama-model-config"),

    # ??????????????????
    path("projects/<uuid:project_id>/quality-radar/", QualityRadarView.as_view(), name="drama-quality-radar"),

    # ???????GET=???POST=???????
    path("projects/<uuid:project_id>/episode-quality/", EpisodeQualityView.as_view(), name="drama-episode-quality"),

    # ????????????? + ?????
    path("projects/<uuid:project_id>/episodes/", EpisodeArtifactView.as_view(), name="drama-episodes"),

    # ?????????100?token?????
    path("projects/<uuid:project_id>/generation-plan/", GenerationPlanView.as_view(), name="drama-generation-plan"),

    # ?? CRUD + ???? + ????
    path("", include(router.urls)),
]
