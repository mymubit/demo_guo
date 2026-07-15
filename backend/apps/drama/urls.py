"""Drama API 路由。"""
from django.urls import path

from apps.drama.views import (
    AdminConfigRollbackView,
    AdminConfigView,
    ArtifactDetailView,
    ExternalScriptReviewView,
    GenerationJobDetailView,
    GenerationJobSSEView,
    GenerationSSEView,
    GenerationStartView,
    GenerationStatusView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectSettingsView,
    StoryBibleApprovalView,
    ThemeMatrixView,
    WorkbenchFormView,
    WorkflowCommandView,
    WorkflowStateView,
)

urlpatterns = [
    path("projects/", ProjectListCreateView.as_view(), name="drama-projects"),
    path("projects/<uuid:project_id>/", ProjectDetailView.as_view(), name="drama-project-detail"),
    path(
        "projects/<uuid:project_id>/settings/",
        ProjectSettingsView.as_view(),
        name="drama-project-settings",
    ),
    path(
        "projects/<uuid:project_id>/workflow/",
        WorkflowStateView.as_view(),
        name="drama-workflow",
    ),
    path(
        "projects/<uuid:project_id>/workflow/commands/",
        WorkflowCommandView.as_view(),
        name="drama-workflow-commands",
    ),
    path(
        "projects/<uuid:project_id>/approvals/story-bible/",
        StoryBibleApprovalView.as_view(),
        name="drama-story-bible-approval",
    ),
    path(
        "projects/<uuid:project_id>/artifacts/<str:artifact_key>/",
        ArtifactDetailView.as_view(),
        name="drama-artifact",
    ),
    path(
        "projects/<uuid:project_id>/generation/start/",
        GenerationStartView.as_view(),
        name="drama-generation-start",
    ),
    path(
        "projects/<uuid:project_id>/generation/<uuid:job_id>/",
        GenerationStatusView.as_view(),
        name="drama-generation-status",
    ),
    path(
        "projects/<uuid:project_id>/generation/<uuid:job_id>/stream/",
        GenerationSSEView.as_view(),
        name="drama-generation-sse",
    ),
    path("jobs/<uuid:job_id>/", GenerationJobDetailView.as_view(), name="drama-job-detail"),
    path(
        "jobs/<uuid:job_id>/stream/",
        GenerationJobSSEView.as_view(),
        name="drama-job-sse",
    ),
    path(
        "external-script-reviews/",
        ExternalScriptReviewView.as_view(),
        name="drama-external-review",
    ),
    path("theme-matrix/", ThemeMatrixView.as_view(), name="drama-theme-matrix"),
    path("meta/workbench-form/", WorkbenchFormView.as_view(), name="drama-workbench-form"),
    path("admin/config/", AdminConfigView.as_view(), name="drama-admin-config"),
    path(
        "admin/config/rollback/",
        AdminConfigRollbackView.as_view(),
        name="drama-admin-config-rollback",
    ),
]
