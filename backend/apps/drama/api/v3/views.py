# -*- coding: utf-8 -*-
"""V3 产品 API 视图。"""
from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.billing_plans import BILLING_PLANS
from apps.drama.api.v3.serializers import (
    CommandRunSerializer,
    CreateProjectSerializer,
    DispatchCommandSerializer,
    ProjectSummarySerializer,
)
from apps.drama.models import V3CommandRun, V3Project
from apps.drama.orchestrator import dispatch_command


def _owned_v3_project(request: Request, project_id) -> V3Project:
    return get_object_or_404(V3Project, id=project_id, owner=request.user)


def _include_archived(request: Request) -> bool:
    raw = (request.query_params.get("include_archived") or "").strip().lower()
    return raw in ("1", "true")


class V3ProjectListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = V3Project.objects.filter(owner=request.user).order_by("-updated_at")
        if not _include_archived(request):
            qs = qs.filter(archived_at__isnull=True)
        items = ProjectSummarySerializer(qs, many=True).data
        return api_response({"items": items})

    def post(self, request: Request) -> Response:
        serializer = CreateProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = dispatch_command(
            owner=request.user,
            command_type="create_project",
            payload=serializer.validated_data,
        )
        if run.status != V3CommandRun.Status.SUCCEEDED or run.project_id is None:
            return api_response(
                {"command_run": CommandRunSerializer(run).data},
                code=1,
                message=run.error_message or "创建项目失败",
                status=400,
            )
        return api_response(ProjectSummarySerializer(run.project).data)


class V3ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        return api_response(ProjectSummarySerializer(project).data)

    def delete(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        project.delete()
        return api_response({"deleted": True, "id": str(project_id)})


class V3ProjectArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        if project.archived_at is None:
            project.archived_at = timezone.now()
            project.save(update_fields=["archived_at", "updated_at"])
        return api_response(ProjectSummarySerializer(project).data)


class V3CommandDispatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = DispatchCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        run = dispatch_command(
            owner=request.user,
            command_type=data["command_type"],
            payload=data.get("payload") or {},
            idempotency_key=data.get("idempotency_key") or "",
        )
        payload: dict = {"command_run": CommandRunSerializer(run).data}
        if run.project_id is not None and run.project is not None:
            payload["project"] = ProjectSummarySerializer(run.project).data
        return api_response(payload)


class V3CommandRunDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, run_id) -> Response:
        run = get_object_or_404(V3CommandRun, id=run_id, owner=request.user)
        return api_response(CommandRunSerializer(run).data)


class V3BillingPlansView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return api_response({"items": BILLING_PLANS})
