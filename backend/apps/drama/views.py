# -*- coding: utf-8 -*-
"""Drama REST API 视图。"""
from __future__ import annotations

import json
import time

from django.conf import settings
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.job_payload import (
    serialize_generation_job,
    sse_event_from_progress,
    sse_heartbeat_event,
    sse_terminal_event,
    sse_timeout_event,
)
from apps.drama.models import DramaGenerationJob, DramaProject
from apps.drama.permissions import (
    DramaConfigReadPermission,
    DramaConfigRollbackPermission,
    DramaConfigWritePermission,
    ProjectApprovePermission,
    ProjectExecutePermission,
    ProjectReadPermission,
    ProjectWritePermission,
)
from apps.drama.serializers import (
    ConfigRollbackSerializer,
    DramaProjectCreateSerializer,
    DramaProjectSerializer,
    ExternalReviewSerializer,
    GenerationStartSerializer,
    StoryBibleApprovalSerializer,
    WorkflowCommandSerializer,
)
from apps.drama.services.artifact_service import ArtifactService
from apps.drama.services.config_overlay import ConfigOverlayService
from apps.drama.services.generation_service import GenerationService
from apps.drama.services.project_settings import ProjectSettingsService
from apps.drama.services.workflow_service import WorkflowService


class ProjectListCreateView(APIView):
    """项目列表与创建。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        projects = DramaProject.objects.filter(owner=request.user)
        data = DramaProjectSerializer(projects, many=True).data
        return api_response(data)

    def post(self, request: Request) -> Response:
        serializer = DramaProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = ProjectSettingsService().create_project(
            request.user,
            serializer.validated_data["title"],
            entry_type=serializer.validated_data["entry_type"],
            episode_count=serializer.validated_data.get("episode_count"),
            core_idea=serializer.validated_data.get("core_idea"),
            external_story=serializer.validated_data.get("external_story"),
        )
        return api_response(
            DramaProjectSerializer(project).data,
            status=status.HTTP_201_CREATED,
        )


class ProjectDetailView(APIView):
    """项目详情、更新、删除。"""

    def get_permissions(self):
        if self.request.method in ("PUT", "DELETE"):
            return [ProjectWritePermission()]
        return [ProjectReadPermission()]

    def get_object(self, project_id: str) -> DramaProject:
        return get_object_or_404(DramaProject, id=project_id)

    def get(self, request: Request, project_id: str) -> Response:
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        return api_response(DramaProjectSerializer(project).data)

    def put(self, request: Request, project_id: str) -> Response:
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        title = request.data.get("title")
        if title:
            project.title = title
            project.save(update_fields=["title", "updated_at"])
        return api_response(DramaProjectSerializer(project).data)

    def delete(self, request: Request, project_id: str) -> Response:
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        project.delete()
        return api_response(None, message="已删除")


class ProjectSettingsView(APIView):
    """项目设置 GET/PUT（If-Match 乐观锁）。"""

    permission_classes = [ProjectReadPermission]

    def get_object(self, project_id: str) -> DramaProject:
        return get_object_or_404(DramaProject, id=project_id)

    def get(self, request: Request, project_id: str) -> Response:
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        settings = ProjectSettingsService().get_settings(project)
        response = api_response(settings)
        response["ETag"] = str(project.settings_revision)
        return response

    def put(self, request: Request, project_id: str) -> Response:
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        if not ProjectWritePermission().has_object_permission(request, self, project):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("无写权限")

        if_match = request.headers.get("If-Match")
        if not if_match:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"If-Match": "必填"})
        expected = int(if_match)

        settings = ProjectSettingsService().update_settings(
            project,
            request.data,
            expected_revision=expected,
            actor=request.user.username,
        )
        project.refresh_from_db()
        response = api_response(settings)
        response["ETag"] = str(project.settings_revision)
        return response


class WorkflowStateView(APIView):
    """流程状态查询。"""

    permission_classes = [ProjectReadPermission]

    def get(self, request: Request, project_id: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        state = WorkflowService().get_state(project)
        return api_response(state)


class WorkflowCommandView(APIView):
    """工作流命令。"""

    permission_classes = [ProjectExecutePermission]

    def post(self, request: Request, project_id: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        serializer = WorkflowCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        state = WorkflowService().apply_command(
            project,
            command_id=data["command_id"],
            event=data["event"],
            expected_version=data["expected_version"],
            payload=data.get("payload"),
            actor=request.user.username,
        )
        return api_response(state)


class StoryBibleApprovalView(APIView):
    """故事蓝图审批。"""

    permission_classes = [ProjectApprovePermission]

    def post(self, request: Request, project_id: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        serializer = StoryBibleApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        state = WorkflowService().approve_story_bible(
            project,
            command_id=data["command_id"],
            decision=data["decision"],
            expected_version=data["expected_version"],
            actor=request.user.username,
        )
        return api_response(state)


class ArtifactDetailView(APIView):
    """产物查询。"""

    permission_classes = [ProjectReadPermission]

    def get(self, request: Request, project_id: str, artifact_key: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        artifact = ArtifactService().get_artifact(project, artifact_key)
        return api_response(artifact)


class ExternalScriptReviewView(APIView):
    """外部剧本审稿。"""

    permission_classes = [ProjectExecutePermission]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request: Request) -> Response:
        content_type = request.content_type or ""
        if content_type.startswith("multipart/"):
            meta = {
                "command_id": request.data.get("command_id", ""),
                "scoring_preset": request.data.get("scoring_preset", "standard"),
                "check_mode": request.data.get("check_mode", "standard"),
                "project_id": request.data.get("project_id"),
            }
            uploaded = request.FILES.get("file")
            if uploaded:
                script_content = uploaded.read().decode("utf-8")
            else:
                script_content = request.data.get("script_content") or request.data.get(
                    "content", ""
                )
        elif "text/plain" in content_type or "text/markdown" in content_type:
            script_content = request.body.decode("utf-8")
            meta = {
                "command_id": request.headers.get("X-Command-Id", ""),
                "scoring_preset": request.headers.get("X-Scoring-Preset", "standard"),
                "check_mode": request.headers.get("X-Check-Mode", "standard"),
            }
        else:
            meta = request.data
            script_content = meta.get("script_content") or meta.get("content", "")

        serializer = ExternalReviewSerializer(data={**meta, "script_content": script_content})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        project = None
        if data.get("project_id"):
            project = get_object_or_404(DramaProject, id=data["project_id"])
            self.check_object_permissions(request, project)

        job = GenerationService().start_external_review(
            command_id=data["command_id"],
            script_content=script_content,
            scoring_preset=data["scoring_preset"],
            check_mode=data["check_mode"],
            actor=request.user.username,
            owner=request.user,
            project=project,
        )
        return api_response(
            serialize_generation_job(job),
            status=status.HTTP_202_ACCEPTED,
        )


class GenerationStartView(APIView):
    """启动生成任务。"""

    permission_classes = [ProjectExecutePermission]

    def post(self, request: Request, project_id: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        serializer = GenerationStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        job = GenerationService().start_generation(
            project,
            command_id=data["command_id"],
            expected_version=data["expected_version"],
            role=data["role"],
            input_payload=data.get("input", {}),
            actor=request.user.username,
        )
        return api_response(
            serialize_generation_job(job),
            status=status.HTTP_202_ACCEPTED,
        )


class GenerationStatusView(APIView):
    """生成任务状态。"""

    permission_classes = [ProjectReadPermission]

    def get(self, request: Request, project_id: str, job_id: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        job = get_object_or_404(DramaGenerationJob, id=job_id, project=project)
        return api_response(serialize_generation_job(job))


class GenerationSSEView(APIView):
    """生成任务 SSE 进度流（项目作用域）。"""

    permission_classes = [ProjectReadPermission]

    def get(self, request: Request, project_id: str, job_id: str) -> StreamingHttpResponse:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        job = get_object_or_404(DramaGenerationJob, id=job_id, project=project)
        return _stream_generation_job(job)


class GenerationJobDetailView(APIView):
    """生成任务状态（无项目上下文，供外部评测等）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, job_id: str) -> Response:
        job = get_object_or_404(DramaGenerationJob, id=job_id)
        _assert_job_access(request, job)
        return api_response(serialize_generation_job(job))


class GenerationJobSSEView(APIView):
    """生成任务 SSE（无项目上下文）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, job_id: str) -> StreamingHttpResponse:
        job = get_object_or_404(DramaGenerationJob, id=job_id)
        _assert_job_access(request, job)
        return _stream_generation_job(job)


def _assert_job_access(request: Request, job: DramaGenerationJob) -> None:
    if job.project_id:
        permission = ProjectReadPermission()
        if not permission.has_object_permission(request, None, job.project):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("无权限访问该任务")
        return
    if job.owner_id and job.owner_id == request.user.id:
        return
    actor = job.request_payload.get("actor")
    if actor == request.user.username:
        return
    from rest_framework.exceptions import PermissionDenied
    raise PermissionDenied("无权限访问该任务")


def _stream_generation_job(job: DramaGenerationJob) -> StreamingHttpResponse:
    heartbeat_interval = settings.GENERATION_SSE_HEARTBEAT_SECONDS
    max_wait = settings.GENERATION_SSE_MAX_WAIT_SECONDS

    def event_stream():
        seen = 0
        started = time.monotonic()
        last_heartbeat = started
        while True:
            now = time.monotonic()
            if now - started >= max_wait:
                payload = json.dumps(
                    sse_timeout_event(job),
                    ensure_ascii=False,
                )
                yield f"data: {payload}\n\n"
                break

            job.refresh_from_db()
            events = job.progress_events or []
            while seen < len(events):
                payload = json.dumps(
                    sse_event_from_progress(job, events[seen]),
                    ensure_ascii=False,
                )
                yield f"data: {payload}\n\n"
                seen += 1
            if job.status in (
                DramaGenerationJob.Status.COMPLETED,
                DramaGenerationJob.Status.FAILED,
                DramaGenerationJob.Status.DISABLED,
            ):
                final = json.dumps(
                    sse_terminal_event(job),
                    ensure_ascii=False,
                )
                yield f"data: {final}\n\n"
                break
            if now - last_heartbeat >= heartbeat_interval:
                payload = json.dumps(
                    sse_heartbeat_event(job),
                    ensure_ascii=False,
                )
                yield f"data: {payload}\n\n"
                last_heartbeat = now
            time.sleep(0.5)

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


class AdminConfigView(APIView):
    """运营配置 GET/PUT。"""

    def get_permissions(self):
        if self.request.method == "GET":
            return [DramaConfigReadPermission()]
        return [DramaConfigWritePermission()]

    def get(self, request: Request) -> Response:
        overlay = ConfigOverlayService().get_current()
        response = api_response(overlay)
        if overlay:
            response["ETag"] = str(overlay.get("audit", {}).get("revision", 0))
        return response

    def put(self, request: Request) -> Response:
        if_match = request.headers.get("If-Match")
        if not if_match:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"If-Match": "必填"})
        overlay = ConfigOverlayService().put_overlay(
            request.data,
            expected_revision=int(if_match),
            actor=request.user.username,
        )
        response = api_response(overlay)
        response["ETag"] = str(overlay["audit"]["revision"])
        return response


class AdminConfigRollbackView(APIView):
    """配置回滚。"""

    permission_classes = [DramaConfigRollbackPermission]

    def post(self, request: Request) -> Response:
        serializer = ConfigRollbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        overlay = ConfigOverlayService().rollback(
            target_revision=data["target_revision"],
            change_reason=data["change_reason"],
            actor=request.user.username,
        )
        return api_response(overlay)


class ThemeMatrixView(APIView):
    """题材矩阵元数据（skills bundle SSOT）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        from apps.drama.services.skills_loader import get_skills_loader

        loader = get_skills_loader()
        manifest = loader.manifest
        rel_path = (manifest.get("configuration_sources") or {}).get(
            "theme", "foundation/theme-matrix.yaml"
        )
        matrix = loader.load_seed_yaml(rel_path)
        return api_response(matrix)
