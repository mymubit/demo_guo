# -*- coding: utf-8 -*-
"""V3 产品 API 路由。"""
from django.urls import path

from apps.drama.api.v3.artifact_views import (
    V3ArtifactListView,
    V3ArtifactRollbackView,
)
from apps.drama.api.v3.blueprint_views import (
    V3BlueprintConfirmView,
    V3BlueprintGenerateView,
    V3BlueprintStateView,
)
from apps.drama.api.v3.delivery_views import (
    V3DeliveryExportDocxView,
    V3DeliveryPrepareView,
    V3DeliveryStateView,
)
from apps.drama.api.v3.episodes_views import (
    V3EpisodesConfirmView,
    V3EpisodesGenerateView,
    V3EpisodesReviseView,
    V3EpisodesStateView,
)
from apps.drama.api.v3.quality_views import (
    V3QualityAcceptView,
    V3QualityComplianceView,
    V3QualityReviseView,
    V3QualityScoreView,
    V3QualityStateView,
)
from apps.drama.api.v3.scripts_views import (
    V3ScriptDraftView,
    V3ScriptEpisodeView,
    V3ScriptsConfirmView,
    V3ScriptsGenerateView,
    V3ScriptsStateView,
)
from apps.drama.api.v3.logs_views import (
    V3LogCallDetailView,
    V3LogRunDetailView,
    V3LogRunListView,
)
from apps.drama.api.v3.models_views import (
    V3ModelProviderActivateView,
    V3ModelProviderDetailView,
    V3ModelProviderKeyDetailView,
    V3ModelProviderKeyListCreateView,
    V3ModelProviderListCreateView,
    V3ModelProviderTestView,
    V3RoleModelMappingView,
)
from apps.drama.api.v3.prices_views import V3ModelPriceDetailView, V3ModelPricesView
from apps.drama.api.v3.system_views import V3SystemConfigView
from apps.drama.api.v3.knowledge_views import (
    V3KnowledgeDocView,
    V3KnowledgeListView,
)
from apps.drama.api.v3.reviews_views import (
    V3ScriptReviewCompareView,
    V3ScriptReviewComplianceView,
    V3ScriptReviewDetailView,
    V3ScriptReviewListCreateView,
    V3ScriptReviewRunDetailView,
    V3ScriptReviewRunListView,
    V3ScriptReviewScoreView,
)
from apps.drama.api.v3.templates_views import (
    V3TemplateCustomCreateView,
    V3TemplateCustomDetailView,
    V3TemplateListView,
)
from apps.drama.api.v3.usage_views import V3UsageSummaryView
from apps.drama.api.v3.topic_views import (
    V3TopicConfirmView,
    V3TopicDraftView,
    V3TopicGenerateView,
    V3TopicStateView,
)
from apps.drama.api.v3.views import (
    V3BillingPlansView,
    V3CommandDispatchView,
    V3CommandRunDetailView,
    V3ProjectArchiveView,
    V3ProjectDetailView,
    V3ProjectListCreateView,
)

urlpatterns = [
    path("projects/", V3ProjectListCreateView.as_view()),
    path("projects/<uuid:project_id>/", V3ProjectDetailView.as_view()),
    path("projects/<uuid:project_id>/archive/", V3ProjectArchiveView.as_view()),
    path("projects/<uuid:project_id>/topic/", V3TopicStateView.as_view()),
    path("projects/<uuid:project_id>/topic/draft/", V3TopicDraftView.as_view()),
    path("projects/<uuid:project_id>/topic/generate/", V3TopicGenerateView.as_view()),
    path("projects/<uuid:project_id>/topic/confirm/", V3TopicConfirmView.as_view()),
    path("projects/<uuid:project_id>/blueprint/", V3BlueprintStateView.as_view()),
    path(
        "projects/<uuid:project_id>/blueprint/generate/",
        V3BlueprintGenerateView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/blueprint/confirm/",
        V3BlueprintConfirmView.as_view(),
    ),
    path("projects/<uuid:project_id>/episodes/", V3EpisodesStateView.as_view()),
    path(
        "projects/<uuid:project_id>/episodes/generate/",
        V3EpisodesGenerateView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/episodes/confirm/",
        V3EpisodesConfirmView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/episodes/revise/",
        V3EpisodesReviseView.as_view(),
    ),
    path("projects/<uuid:project_id>/scripts/", V3ScriptsStateView.as_view()),
    path(
        "projects/<uuid:project_id>/scripts/generate/",
        V3ScriptsGenerateView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/scripts/confirm/",
        V3ScriptsConfirmView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/scripts/<int:episode_number>/",
        V3ScriptEpisodeView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/scripts/<int:episode_number>/draft/",
        V3ScriptDraftView.as_view(),
    ),
    path("projects/<uuid:project_id>/quality/", V3QualityStateView.as_view()),
    path(
        "projects/<uuid:project_id>/quality/score/",
        V3QualityScoreView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/quality/compliance/",
        V3QualityComplianceView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/quality/accept/",
        V3QualityAcceptView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/quality/revise/",
        V3QualityReviseView.as_view(),
    ),
    path("projects/<uuid:project_id>/delivery/", V3DeliveryStateView.as_view()),
    path(
        "projects/<uuid:project_id>/delivery/prepare/",
        V3DeliveryPrepareView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/delivery/export/docx/",
        V3DeliveryExportDocxView.as_view(),
    ),
    path("projects/<uuid:project_id>/artifacts/", V3ArtifactListView.as_view()),
    path(
        "projects/<uuid:project_id>/artifacts/rollback/",
        V3ArtifactRollbackView.as_view(),
    ),
    path("commands/", V3CommandDispatchView.as_view()),
    path("commands/<uuid:run_id>/", V3CommandRunDetailView.as_view()),
    path("billing/plans/", V3BillingPlansView.as_view()),
    path("system/config/", V3SystemConfigView.as_view()),
    path("models/providers/", V3ModelProviderListCreateView.as_view()),
    path(
        "models/providers/<uuid:provider_id>/",
        V3ModelProviderDetailView.as_view(),
    ),
    path(
        "models/providers/<uuid:provider_id>/activate/",
        V3ModelProviderActivateView.as_view(),
    ),
    path(
        "models/providers/<uuid:provider_id>/test/",
        V3ModelProviderTestView.as_view(),
    ),
    path(
        "models/providers/<uuid:provider_id>/keys/",
        V3ModelProviderKeyListCreateView.as_view(),
    ),
    path(
        "models/providers/<uuid:provider_id>/keys/<uuid:key_id>/",
        V3ModelProviderKeyDetailView.as_view(),
    ),
    path("models/role-mappings/", V3RoleModelMappingView.as_view()),
    path("models/prices/", V3ModelPricesView.as_view()),
    path("models/prices/<int:price_id>/", V3ModelPriceDetailView.as_view()),
    path("usage/summary/", V3UsageSummaryView.as_view()),
    path("logs/runs/", V3LogRunListView.as_view()),
    path("logs/runs/<uuid:run_id>/", V3LogRunDetailView.as_view()),
    path("logs/calls/<uuid:call_id>/", V3LogCallDetailView.as_view()),
    path("templates/", V3TemplateListView.as_view()),
    path("templates/custom/", V3TemplateCustomCreateView.as_view()),
    path(
        "templates/custom/<uuid:template_id>/",
        V3TemplateCustomDetailView.as_view(),
    ),
    path("knowledge/", V3KnowledgeListView.as_view()),
    path("knowledge/doc/", V3KnowledgeDocView.as_view()),
    path("reviews/", V3ScriptReviewListCreateView.as_view()),
    path("reviews/<uuid:review_id>/", V3ScriptReviewDetailView.as_view()),
    path("reviews/<uuid:review_id>/score/", V3ScriptReviewScoreView.as_view()),
    path(
        "reviews/<uuid:review_id>/compliance/",
        V3ScriptReviewComplianceView.as_view(),
    ),
    path("reviews/<uuid:review_id>/runs/", V3ScriptReviewRunListView.as_view()),
    path(
        "reviews/<uuid:review_id>/runs/<uuid:run_id>/",
        V3ScriptReviewRunDetailView.as_view(),
    ),
    path(
        "reviews/<uuid:review_id>/compare/",
        V3ScriptReviewCompareView.as_view(),
    ),
]
