# -*- coding: utf-8 -*-
"""
创作模块路由

前缀 /api/creation/
"""

from django.urls import path

from .views import (
    AiFieldGenerateView,
    CreationSubmitView,
    CreationProgressView,
    CreationDownloadView,
    CreationDownloadByTokenView,
    CreationShareCreateView,
    ShareView,
    CreationWorkspaceView,
    IndependentAgentRunDetailView,
    IndependentAgentRunListView,
    IndependentAgentRunView,
    IndependentAgentEstimateView,
    ProjectArtifactView,
)
from .views_stream import (
    IndependentAgentStreamView,
    ProjectAgentNotesView,
    ProjectChunksContinueView,
    ProjectChunksView,
)
from .fusion_views import (
    AgentCatalogView,
    AgentWorkspaceCatalogView,
    FusionCatalogView,
    FusionNodesView,
)

app_name = "creation"

urlpatterns = [
    path("agents/catalog/", AgentCatalogView.as_view(), name="creation-agent-catalog"),
    path(
        "agents/workspace-catalog/",
        AgentWorkspaceCatalogView.as_view(),
        name="creation-agent-workspace-catalog",
    ),
    path("fusion/catalog/", FusionCatalogView.as_view(), name="creation-fusion-catalog"),
    path("fusion/nodes/", FusionNodesView.as_view(), name="creation-fusion-nodes"),
    path(
        "projects/<str:project_id>/workspace/",
        CreationWorkspaceView.as_view(),
        name="creation-workspace",
    ),
    path(
        "projects/<str:project_id>/agents/<str:agent_id>/run/",
        IndependentAgentRunView.as_view(),
        name="creation-independent-agent-run",
    ),
    path(
        "projects/<str:project_id>/agents/<str:agent_id>/estimate/",
        IndependentAgentEstimateView.as_view(),
        name="creation-independent-agent-estimate",
    ),
    path(
        "projects/<str:project_id>/agents/<str:agent_id>/runs/",
        IndependentAgentRunListView.as_view(),
        name="creation-independent-agent-runs",
    ),
    path(
        "projects/<str:project_id>/runs/<str:run_id>/",
        IndependentAgentRunDetailView.as_view(),
        name="creation-independent-run-detail",
    ),
    path(
        "projects/<str:project_id>/artifacts/<str:artifact_key>/",
        ProjectArtifactView.as_view(),
        name="creation-project-artifact",
    ),
    path(
        "projects/<str:project_id>/agents/<str:agent_id>/stream/",
        IndependentAgentStreamView.as_view(),
        name="creation-independent-agent-stream",
    ),
    path(
        "projects/<str:project_id>/chunks/",
        ProjectChunksView.as_view(),
        name="creation-project-chunks",
    ),
    path(
        "projects/<str:project_id>/chunks/continue/",
        ProjectChunksContinueView.as_view(),
        name="creation-project-chunks-continue",
    ),
    path(
        "projects/<str:project_id>/agent-notes/",
        ProjectAgentNotesView.as_view(),
        name="creation-project-agent-notes",
    ),
    path("submit/", CreationSubmitView.as_view(), name="creation-submit"),
    path("ai/generate/", AiFieldGenerateView.as_view(), name="creation-ai-generate"),
    path(
        "progress/<str:project_id>/",
        CreationProgressView.as_view(),
        name="creation-progress",
    ),
    path(
        "download/<str:project_id>/",
        CreationDownloadView.as_view(),
        name="creation-download",
    ),
    path(
        "dl/<str:token>/",
        CreationDownloadByTokenView.as_view(),
        name="creation-download-by-token",
    ),
    path(
        "share/<str:project_id>/",
        CreationShareCreateView.as_view(),
        name="creation-share-create",
    ),
    path(
        "share/view/<str:token>/",
        ShareView.as_view(),
        name="creation-share-view",
    ),
]
