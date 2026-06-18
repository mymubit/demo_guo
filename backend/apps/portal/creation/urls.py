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
    CreationNodeConfirmView,
    CreationNodeRegenerateView,
    CreationWorkspaceView,
    CreationAgentGenerateView,
    CreationAgentContentView,
    CreationAgentQualityAlertAckView,
    IndependentAgentRunDetailView,
    IndependentAgentRunListView,
    IndependentAgentRunView,
    IndependentAgentEstimateView,
    ProjectArtifactView,
)
from .fusion_views import (
    AgentCatalogView,
    AgentWorkspaceCatalogView,
    CreationNodePreviewView,
    FusionArtifactView,
    FusionCatalogView,
    FusionNodesView,
    FusionSnapshotView,
)
from .sse_views import CreationProgressStreamView

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
        "fusion/<str:project_id>/",
        FusionSnapshotView.as_view(),
        name="creation-fusion-snapshot",
    ),
    path(
        "fusion/<str:project_id>/artifacts/<str:artifact_key>/",
        FusionArtifactView.as_view(),
        name="creation-fusion-artifact",
    ),
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
        "projects/<str:project_id>/agents/<int:node_index>/quality-alert/ack/",
        CreationAgentQualityAlertAckView.as_view(),
        name="creation-agent-quality-alert-ack",
    ),
    path(
        "projects/<str:project_id>/agents/<int:node_index>/content/",
        CreationAgentContentView.as_view(),
        name="creation-agent-content",
    ),
    path(
        "projects/<str:project_id>/agents/<int:node_index>/generate/",
        CreationAgentGenerateView.as_view(),
        name="creation-agent-generate",
    ),
    path(
        "projects/<str:project_id>/nodes/<int:node_index>/preview/",
        CreationNodePreviewView.as_view(),
        name="creation-node-preview",
    ),
    # 提交创作
    path("submit/", CreationSubmitView.as_view(), name="creation-submit"),
    path("ai/generate/", AiFieldGenerateView.as_view(), name="creation-ai-generate"),
    # 查询进度（轮询方式，保持兼容）
    path(
        "progress/<str:project_id>/",
        CreationProgressView.as_view(),
        name="creation-progress",
    ),
    # SSE 实时进度推送（P2，替代自适应轮询）
    path(
        "projects/<str:project_id>/progress/stream/",
        CreationProgressStreamView.as_view(),
        name="creation-progress-stream",
    ),
    path(
        "projects/<str:project_id>/confirm/",
        CreationNodeConfirmView.as_view(),
        name="creation-node-confirm",
    ),
    path(
        "projects/<str:project_id>/regenerate/",
        CreationNodeRegenerateView.as_view(),
        name="creation-node-regenerate",
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
