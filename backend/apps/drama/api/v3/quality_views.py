# -*- coding: utf-8 -*-
"""V3 质检 Quality REST API。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.serializers import (
    ArtifactVersionSerializer,
    CommandRunSerializer,
    QualityAcceptSerializer,
    QualityFindingSerializer,
    QualityReviseSerializer,
)
from apps.drama.api.v3.views import _owned_v3_project
from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3QualityFinding
from apps.drama.orchestrator import dispatch_command
from apps.drama.orchestrator.artifacts import latest
from apps.drama.orchestrator.report_meta import is_report_stale

_QUALITY_KEY = "quality_report"
_COMPLIANCE_KEY = "compliance_report"
_SCRIPTS_KEY = "episode_scripts"

_QUALITY_RUN_COMMANDS = (
    "score_quality",
    "revise_from_findings",
    "accept_findings",
)
_COMPLIANCE_RUN_COMMANDS = ("check_compliance",)


def _serialize_artifact(art: V3ArtifactVersion | None) -> dict | None:
    if art is None:
        return None
    return ArtifactVersionSerializer(art).data


def _latest_run(project, command_types: tuple[str, ...]) -> V3CommandRun | None:
    return (
        V3CommandRun.objects.filter(project=project, command_type__in=command_types)
        .order_by("-created_at")
        .first()
    )


def _report_is_stale(
    report: V3ArtifactVersion | None,
    scripts: V3ArtifactVersion | None,
) -> bool:
    if report is None:
        return False
    payload = report.payload if isinstance(report.payload, dict) else {}
    return is_report_stale(report_payload=payload, current_script=scripts)


def _quality_state(project) -> dict:
    scripts = latest(
        project, _SCRIPTS_KEY, status=V3ArtifactVersion.Status.COMMITTED
    )
    quality = latest(
        project, _QUALITY_KEY, status=V3ArtifactVersion.Status.COMMITTED
    )
    compliance = latest(
        project, _COMPLIANCE_KEY, status=V3ArtifactVersion.Status.COMMITTED
    )
    findings = V3QualityFinding.objects.filter(project=project).order_by(
        "source", "finding_key"
    )
    quality_run = _latest_run(project, _QUALITY_RUN_COMMANDS)
    compliance_run = _latest_run(project, _COMPLIANCE_RUN_COMMANDS)
    return {
        "stage": project.stage,
        "quality_report": _serialize_artifact(quality),
        "compliance_report": _serialize_artifact(compliance),
        "findings": QualityFindingSerializer(findings, many=True).data,
        "quality_is_stale": _report_is_stale(quality, scripts),
        "compliance_is_stale": _report_is_stale(compliance, scripts),
        "latest_quality_run": (
            CommandRunSerializer(quality_run).data if quality_run is not None else None
        ),
        "latest_compliance_run": (
            CommandRunSerializer(compliance_run).data
            if compliance_run is not None
            else None
        ),
    }


class V3QualityStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        return api_response(_quality_state(project))


class V3QualityScoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        run = dispatch_command(
            owner=request.user,
            command_type="score_quality",
            payload={"project_id": str(project.id)},
        )
        return api_response({"command_run": CommandRunSerializer(run).data})


class V3QualityComplianceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        run = dispatch_command(
            owner=request.user,
            command_type="check_compliance",
            payload={"project_id": str(project.id)},
        )
        return api_response({"command_run": CommandRunSerializer(run).data})


class V3QualityAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = QualityAcceptSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        run = dispatch_command(
            owner=request.user,
            command_type="accept_findings",
            payload={
                "project_id": str(project.id),
                "findings": serializer.validated_data["findings"],
            },
        )
        return api_response({"command_run": CommandRunSerializer(run).data})


class V3QualityReviseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = QualityReviseSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        payload: dict = {"project_id": str(project.id)}
        if "finding_keys" in serializer.validated_data:
            payload["finding_keys"] = serializer.validated_data["finding_keys"]
        if "episode_range" in serializer.validated_data:
            payload["episode_range"] = serializer.validated_data["episode_range"]
        run = dispatch_command(
            owner=request.user,
            command_type="revise_from_findings",
            payload=payload,
        )
        return api_response({"command_run": CommandRunSerializer(run).data})
