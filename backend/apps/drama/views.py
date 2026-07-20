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

from apps.core.exceptions import SCHEMA_VALIDATION_FAILED, VALIDATION_ERROR, BusinessException
from apps.core.responses import api_response
from apps.drama.job_payload import (
    serialize_generation_job,
    sse_event_from_progress,
    sse_heartbeat_event,
    sse_terminal_event,
    sse_timeout_event,
)
from apps.drama.models import DramaGenerationJob, DramaLlmCallLog, DramaProject
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
    LlmProviderUpdateSerializer,
    LlmProviderWriteSerializer,
    GenerationStartSerializer,
    StoryBibleApprovalSerializer,
    WorkflowCommandSerializer,
)
from apps.drama.sse_renderers import EventStreamRenderer
from apps.drama.services.artifact_service import ArtifactService
from apps.drama.services.config_overlay import ConfigOverlayService
from apps.drama.services.generation_service import GenerationService
from apps.drama.services.llm_call_context import llm_call_scope
from apps.drama.services.llm_call_log_service import LlmCallLogService
from apps.drama.services.llm_config_service import LlmConfigService
from apps.drama.services.llm_provider import LlmProvider, LlmProviderError
from apps.drama.services.project_settings import ProjectSettingsService
from apps.drama.services.skill_ops_service import export_skill_failures, skill_ops_overview
from apps.drama.services.skills_inventory_service import (
    build_prompt_breakdown,
    build_role_bundle_content,
    build_skills_inventory,
    read_skills_content,
)
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

    def get(self, request: Request) -> Response:
        """列出当前用户最近的外部评测任务（刷新页面可恢复）。"""
        try:
            limit = int(request.query_params.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        limit = min(max(limit, 1), 50)
        jobs = (
            DramaGenerationJob.objects.filter(
                owner=request.user,
                project__isnull=True,
                job_type__in=[
                    DramaGenerationJob.JobType.EXTERNAL_REVIEW,
                    DramaGenerationJob.JobType.PARALLEL_JUDGE,
                ],
            )
            .order_by("-updated_at")[:limit]
        )
        items = [serialize_generation_job(job) for job in jobs]
        return api_response({"items": items, "total": len(items)})

    def post(self, request: Request) -> Response:
        content_type = request.content_type or ""
        if content_type.startswith("multipart/"):
            meta = {
                "command_id": request.data.get("command_id", ""),
                "scoring_preset": request.data.get("scoring_preset", "standard"),
                "check_mode": request.data.get("check_mode", "standard"),
                "script_title": request.data.get("script_title", ""),
                "source_filename": request.data.get("source_filename") or "",
            }
            # FormData 未带字段时 get 为 None；UUIDField 默认不允许 null，勿写入空值
            raw_project_id = request.data.get("project_id")
            if raw_project_id not in (None, ""):
                meta["project_id"] = raw_project_id
            uploaded = request.FILES.get("file")
            if uploaded:
                raw = uploaded.read()
                try:
                    script_content = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    script_content = raw.decode("gbk", errors="replace")
                if not meta["source_filename"]:
                    meta["source_filename"] = getattr(uploaded, "name", "") or ""
            else:
                script_content = request.data.get("script_content") or ""
        elif "text/plain" in content_type or "text/markdown" in content_type:
            script_content = request.body.decode("utf-8")
            meta = {
                "command_id": request.headers.get("X-Command-Id", ""),
                "scoring_preset": request.headers.get("X-Scoring-Preset", "standard"),
                "check_mode": request.headers.get("X-Check-Mode", "standard"),
                "script_title": request.headers.get("X-Script-Title", ""),
                "source_filename": request.headers.get("X-Source-Filename", ""),
            }
        else:
            meta = request.data
            script_content = meta.get("script_content") or ""

        serializer = ExternalReviewSerializer(data={**meta, "script_content": script_content})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        project = None
        if data.get("project_id"):
            project = get_object_or_404(DramaProject, id=data["project_id"])
            self.check_object_permissions(request, project)

        source_filename = (data.get("source_filename") or "").strip()
        script_title = (data.get("script_title") or "").strip()

        job = GenerationService().start_external_review(
            command_id=data["command_id"],
            script_content=script_content,
            scoring_preset=data["scoring_preset"],
            check_mode=data["check_mode"],
            actor=request.user.username,
            owner=request.user,
            project=project,
            source_filename=source_filename,
            script_title=script_title,
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


class GenerationLatestView(APIView):
    """查询项目下某角色/产物的最近一次生成任务（用于回页恢复进度或展示失败原因）。"""

    permission_classes = [ProjectReadPermission]

    def get(self, request: Request, project_id: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        qs = DramaGenerationJob.objects.filter(project=project).order_by("-created_at")
        role = (request.query_params.get("role") or "").strip()
        artifact_key = (request.query_params.get("artifact_key") or "").strip()
        if role:
            qs = qs.filter(role=role)
        if artifact_key:
            qs = qs.filter(artifact_key=artifact_key)
        job = qs.first()
        if job is None:
            return api_response(None)
        job = GenerationService().fail_if_stale(job)
        return api_response(serialize_generation_job(job))


class GenerationStatusView(APIView):
    """生成任务状态。"""

    permission_classes = [ProjectReadPermission]

    def get(self, request: Request, project_id: str, job_id: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        job = get_object_or_404(DramaGenerationJob, id=job_id, project=project)
        job = GenerationService().fail_if_stale(job)
        return api_response(serialize_generation_job(job))


class GenerationAbandonView(APIView):
    """手动结束卡住的进行中任务，便于重新执行阶段。"""

    permission_classes = [ProjectExecutePermission]

    def post(self, request: Request, project_id: str, job_id: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        job = get_object_or_404(DramaGenerationJob, id=job_id, project=project)
        if job.status in (
            DramaGenerationJob.Status.COMPLETED,
            DramaGenerationJob.Status.FAILED,
            DramaGenerationJob.Status.DISABLED,
        ):
            return api_response(serialize_generation_job(job))
        updated = GenerationService().abandon_job(
            job,
            actor=request.user.username,
        )
        return api_response(serialize_generation_job(updated))


class GenerationSSEView(APIView):
    """生成任务 SSE 进度流（项目作用域）。"""

    permission_classes = [ProjectReadPermission]
    renderer_classes = [EventStreamRenderer]

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
        job = GenerationService().fail_if_stale(job)
        return api_response(serialize_generation_job(job))

    def delete(self, request: Request, job_id: str) -> Response:
        """删除当前用户的外部评测记录（不可恢复）。"""
        job = get_object_or_404(DramaGenerationJob, id=job_id)
        _assert_job_access(request, job)
        if job.project_id is not None:
            raise BusinessException(
                VALIDATION_ERROR,
                "项目内生成任务不可在此删除",
                http_status=400,
            )
        if job.job_type not in (
            DramaGenerationJob.JobType.EXTERNAL_REVIEW,
            DramaGenerationJob.JobType.PARALLEL_JUDGE,
        ):
            raise BusinessException(
                VALIDATION_ERROR,
                "仅外部评测记录可删除",
                http_status=400,
            )
        if job.status in (
            DramaGenerationJob.Status.PENDING,
            DramaGenerationJob.Status.QUEUED,
            DramaGenerationJob.Status.RUNNING,
        ):
            raise BusinessException(
                VALIDATION_ERROR,
                "进行中的评测暂不可删除，请等待结束后再删",
                http_status=409,
            )
        job.delete()
        return api_response({"deleted": True, "job_id": str(job_id)})


class GenerationJobReprocessView(APIView):
    """用已有 LLM 调用日志重新解析落库（不重新调用模型）。"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, job_id: str) -> Response:
        job = get_object_or_404(DramaGenerationJob, id=job_id)
        _assert_job_access(request, job)
        updated = GenerationService().reprocess_review_from_llm_logs(job)
        return api_response(serialize_generation_job(updated))


class GenerationJobSSEView(APIView):
    """生成任务 SSE（无项目上下文）。"""

    permission_classes = [IsAuthenticated]
    renderer_classes = [EventStreamRenderer]

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
                    sse_event_from_progress(
                        job,
                        events[seen],
                        events_prefix=events[: seen + 1],
                    ),
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
        overlay = ConfigOverlayService().get_current_or_empty()
        response = api_response(overlay)
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


class WorkbenchFormView(APIView):
    """工作台动态表单契约（集中 parameters/artifacts 合并导出）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        from apps.drama.services.skills_loader import get_skills_loader

        loader = get_skills_loader()
        return api_response(loader.export_workbench_form())


class SkillsInventoryView(APIView):
    """角色 ↔ 原子技能装配库存（静态字数 + 反向索引）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return api_response(build_skills_inventory())


class RolePromptBreakdownView(APIView):
    """角色 system prompt 分层字数（可选按项目设定 dry-run）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, agent_id: str) -> Response:
        from apps.drama.services.skills_loader import get_skills_loader

        loader = get_skills_loader()
        try:
            loader.get_role_entry(agent_id)
        except KeyError as exc:
            raise BusinessException(VALIDATION_ERROR, str(exc)) from exc

        project_id = (request.query_params.get("project_id") or "").strip()
        settings: dict = {}
        project_uuid = None
        if project_id:
            project = get_object_or_404(DramaProject, id=project_id, owner=request.user)
            settings = dict(project.settings or {})
            project_uuid = str(project.id)

        data = build_prompt_breakdown(agent_id, settings=settings, loader=loader)
        data["project_id"] = project_uuid
        data["settings_mode"] = "project" if project_id else "default"
        return api_response(data)


class SkillsContentView(APIView):
    """技能仓正文按需读取（module / role_skill / path / role_rules）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        kind = (request.query_params.get("kind") or "").strip()
        try:
            data = read_skills_content(
                kind=kind,
                module_id=request.query_params.get("id"),
                agent_id=request.query_params.get("agent_id"),
                path=request.query_params.get("path"),
            )
        except ValueError as exc:
            raise BusinessException(VALIDATION_ERROR, str(exc)) from exc
        except KeyError as exc:
            raise BusinessException(VALIDATION_ERROR, str(exc)) from exc
        except FileNotFoundError as exc:
            raise BusinessException(VALIDATION_ERROR, str(exc)) from exc
        return api_response(data)


class RoleBundleContentView(APIView):
    """角色挂载全文（SKILL / 模块 / 知识 / 规则等）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, agent_id: str) -> Response:
        try:
            data = build_role_bundle_content(agent_id)
        except KeyError as exc:
            raise BusinessException(VALIDATION_ERROR, str(exc)) from exc
        except FileNotFoundError as exc:
            raise BusinessException(VALIDATION_ERROR, str(exc)) from exc
        return api_response(data)


class AdminLlmProviderListCreateView(APIView):
    """LLM Provider 列表 / 创建。"""

    def get_permissions(self):
        if self.request.method == "GET":
            return [DramaConfigReadPermission()]
        return [DramaConfigWritePermission()]

    def get(self, request: Request) -> Response:
        resolved = LlmConfigService.resolve()
        return api_response(
            {
                "runtime": {
                    "status": LlmProvider.status().value,
                    "source": resolved.source,
                    "model": resolved.model if resolved.enabled else "",
                    "base_url": resolved.base_url if resolved.enabled else "",
                    "api_key_set": bool(resolved.api_key),
                },
                "providers": LlmConfigService.list_providers(),
            }
        )

    def post(self, request: Request) -> Response:
        serializer = LlmProviderWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = LlmConfigService.create_provider(
            dict(serializer.validated_data),
            actor=request.user.username,
        )
        return api_response(
            LlmConfigService.serialize_provider(obj),
            status=status.HTTP_201_CREATED,
        )


class AdminLlmProviderDetailView(APIView):
    """LLM Provider 更新 / 删除。"""

    def get_permissions(self):
        if self.request.method == "GET":
            return [DramaConfigReadPermission()]
        return [DramaConfigWritePermission()]

    def get(self, request: Request, provider_id) -> Response:
        from apps.drama.models import DramaLlmProvider

        obj = get_object_or_404(DramaLlmProvider, pk=provider_id)
        return api_response(LlmConfigService.serialize_provider(obj))

    def put(self, request: Request, provider_id) -> Response:
        serializer = LlmProviderUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = LlmConfigService.update_provider(
            provider_id,
            dict(serializer.validated_data),
            actor=request.user.username,
        )
        return api_response(LlmConfigService.serialize_provider(obj))

    def delete(self, request: Request, provider_id) -> Response:
        LlmConfigService.delete_provider(provider_id, actor=request.user.username)
        return api_response(None)


class AdminLlmProviderActivateView(APIView):
    """设为当前使用的 LLM。"""

    permission_classes = [DramaConfigWritePermission]

    def post(self, request: Request, provider_id) -> Response:
        obj = LlmConfigService.activate(provider_id, actor=request.user.username)
        return api_response(LlmConfigService.serialize_provider(obj))


class AdminLlmProviderTestView(APIView):
    """连通性探测（使用指定配置或当前生效配置）。

    优先 GET /models（通常百毫秒级），避免用 chat/completions 做探测——后者偶发数秒～超时。
    """

    permission_classes = [DramaConfigWritePermission]
    # 探测专用短超时：能通则很快返回，不通也不要挂几十秒
    _PROBE_TIMEOUT = (5, 15)

    def post(self, request: Request, provider_id=None) -> Response:
        from apps.drama.models import DramaLlmProvider
        from apps.drama.services.secret_crypto import decrypt_secret

        if provider_id:
            obj = get_object_or_404(DramaLlmProvider, pk=provider_id)
            base_url = obj.base_url
            api_key = decrypt_secret(obj.api_key_encrypted) or ""
            model = obj.model_name
        else:
            cfg = LlmConfigService.resolve()
            base_url, api_key, model = cfg.base_url, cfg.api_key, cfg.model

        if not base_url or not api_key:
            return api_response(
                {"ok": False, "error": "Base URL 或 API Key 未配置"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base = base_url.rstrip("/")
        models_url = f"{base}/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        probe_desc = "GET /models"
        started = time.monotonic()

        with llm_call_scope(
            purpose=DramaLlmCallLog.Purpose.CONNECTIVITY_TEST,
            actor=request.user.username,
            role="admin.connectivity-test",
        ):
            try:
                requests_mod = __import__("requests")
                resp = requests_mod.get(
                    models_url,
                    headers=headers,
                    timeout=self._PROBE_TIMEOUT,
                )
                # 部分厂商无 /models：404/405 时降级为极短 chat 探测
                if resp.status_code in (404, 405):
                    probe_desc = "POST /chat/completions (max_tokens=1)"
                    resp = requests_mod.post(
                        LlmProvider._chat_url(base),
                        headers=headers,
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": "ping"}],
                            "max_tokens": 1,
                        },
                        timeout=self._PROBE_TIMEOUT,
                    )

                latency_ms = int((time.monotonic() - started) * 1000)
                ok = resp.status_code < 400
                response_json = None
                try:
                    response_json = resp.json()
                except ValueError:
                    response_json = None

                model_hint = ""
                if ok and isinstance(response_json, dict) and model:
                    ids = {
                        str(item.get("id") or "")
                        for item in (response_json.get("data") or [])
                        if isinstance(item, dict)
                    }
                    if ids and model not in ids:
                        model_hint = f"；当前模型「{model}」未出现在 models 列表（可能是推理接入点 ID，属正常）"

                detail = f"{probe_desc} → HTTP {resp.status_code}，耗时 {latency_ms}ms{model_hint}"
                if not ok:
                    detail = f"{detail}；{(resp.text or '')[:200]}"

                LlmCallLogService.record(
                    system_prompt="",
                    user_prompt=probe_desc,
                    model_name=model,
                    base_url=base_url,
                    status=DramaLlmCallLog.Status.SUCCESS if ok else DramaLlmCallLog.Status.ERROR,
                    latency_ms=latency_ms,
                    http_status=resp.status_code,
                    response_json=response_json if isinstance(response_json, dict) else None,
                    response_text=(resp.text or "")[:2000],
                    error_message="" if ok else (resp.text or "")[:2000],
                    purpose=DramaLlmCallLog.Purpose.CONNECTIVITY_TEST,
                    role="admin.connectivity-test",
                    actor=request.user.username,
                )
                return api_response(
                    {
                        "ok": ok,
                        "status_code": resp.status_code,
                        "latency_ms": latency_ms,
                        "probe": probe_desc,
                        "detail": detail,
                        "message": "连通成功" if ok else "连通失败",
                    }
                )
            except Exception as exc:  # noqa: BLE001
                latency_ms = int((time.monotonic() - started) * 1000)
                err = str(exc)
                LlmCallLogService.record(
                    system_prompt="",
                    user_prompt=probe_desc,
                    model_name=model,
                    base_url=base_url,
                    status=DramaLlmCallLog.Status.ERROR,
                    latency_ms=latency_ms,
                    error_message=err,
                    purpose=DramaLlmCallLog.Purpose.CONNECTIVITY_TEST,
                    role="admin.connectivity-test",
                    actor=request.user.username,
                )
                return api_response(
                    {
                        "ok": False,
                        "error": err,
                        "latency_ms": latency_ms,
                        "probe": probe_desc,
                        "message": "连通失败",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )


class ProjectLlmCallLogListView(APIView):
    """项目 LLM 调用链日志（摘要列表）。"""

    permission_classes = [ProjectReadPermission]

    def get(self, request: Request, project_id: str) -> Response:
        project = get_object_or_404(DramaProject, id=project_id)
        self.check_object_permissions(request, project)
        job_id = request.query_params.get("job_id")
        role = request.query_params.get("role")
        try:
            limit = min(int(request.query_params.get("limit", "50")), 200)
        except ValueError:
            limit = 50
        logs = LlmCallLogService.list_for_project(
            project,
            job_id=job_id,
            role=role,
            limit=limit,
        )
        return api_response(
            {
                "items": [LlmCallLogService.serialize_summary(log) for log in logs],
                "count": len(logs),
            }
        )


class LlmCallLogDetailView(APIView):
    """单条 LLM 调用详情（含完整 prompt / response）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, log_id: str) -> Response:
        log = get_object_or_404(
            DramaLlmCallLog.objects.select_related("project", "generation_job"),
            pk=log_id,
        )
        if log.project_id:
            permission = ProjectReadPermission()
            if not permission.has_object_permission(request, self, log.project):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("无权查看")
        elif log.generation_job_id:
            _assert_job_access(request, log.generation_job)
        elif not request.user.is_staff:
            return api_response(None, message="无权查看", status=status.HTTP_403_FORBIDDEN)
        return api_response(LlmCallLogService.serialize_detail(log))


class GenerationJobLlmCallLogListView(APIView):
    """按生成任务查看 LLM 调用链（含外部评测无项目任务；任务所有者可看）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, job_id: str) -> Response:
        job = get_object_or_404(DramaGenerationJob, id=job_id)
        _assert_job_access(request, job)
        role = request.query_params.get("role")
        try:
            limit = min(int(request.query_params.get("limit", "50")), 100)
        except ValueError:
            limit = 50
        include_detail = str(request.query_params.get("detail", "1")).lower() in {
            "1",
            "true",
            "yes",
        }
        logs = LlmCallLogService.list_for_job(job, role=role, limit=limit)
        serialize = (
            LlmCallLogService.serialize_detail
            if include_detail
            else LlmCallLogService.serialize_summary
        )
        return api_response(
            {
                "items": [serialize(log) for log in logs],
                "count": len(logs),
            }
        )


class AdminLlmCallLogListView(APIView):
    """运营：全局 LLM 调用日志检索。"""

    permission_classes = [DramaConfigReadPermission]

    def get(self, request: Request) -> Response:
        try:
            limit = min(int(request.query_params.get("limit", "100")), 300)
        except ValueError:
            limit = 100
        logs = LlmCallLogService.list_global(
            project_id=request.query_params.get("project_id"),
            job_id=request.query_params.get("job_id"),
            role=request.query_params.get("role"),
            status=request.query_params.get("status"),
            limit=limit,
        )
        return api_response(
            {
                "items": [LlmCallLogService.serialize_summary(log) for log in logs],
                "count": len(logs),
            }
        )


class AdminSkillOpsOverviewView(APIView):
    """技能运维总览：失败样本 + 离线评测摘要 + 纠错粗统计。"""

    # 单人使用阶段：登录即可；后续可收紧为 DramaConfigReadPermission
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        try:
            limit = min(int(request.query_params.get("limit", "30")), 100)
        except ValueError:
            limit = 30
        role = (request.query_params.get("role") or "").strip()
        return api_response(skill_ops_overview(limit=limit, role=role))


class AdminSkillOpsExportView(APIView):
    """导出技能失败样本（供写入 anti-examples）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        try:
            limit = min(int(request.query_params.get("limit", "50")), 200)
        except ValueError:
            limit = 50
        role = (request.query_params.get("role") or "").strip()
        rows = export_skill_failures(limit=limit, role=role)
        return api_response({"items": rows, "count": len(rows)})
