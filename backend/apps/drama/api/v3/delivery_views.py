# -*- coding: utf-8 -*-
"""V3 交付 Delivery REST API。"""
from __future__ import annotations

from io import BytesIO

from django.http import FileResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_error, api_response
from apps.drama.api.v3.serializers import ArtifactVersionSerializer, CommandRunSerializer
from apps.drama.api.v3.views import _owned_v3_project
from apps.drama.models import V3ArtifactVersion, V3CommandRun
from apps.drama.orchestrator import dispatch_command
from apps.drama.orchestrator.artifacts import latest
from apps.drama.orchestrator.delivery_gate import evaluate_delivery_gate
from apps.drama.orchestrator.docx_export import build_episode_scripts_docx

_PACKAGE_KEY = "production_package"
_SCRIPTS_KEY = "episode_scripts"
_DELIVERY_RUN_COMMANDS = ("prepare_delivery",)
_DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def _serialize_artifact(art: V3ArtifactVersion | None) -> dict | None:
    if art is None:
        return None
    return ArtifactVersionSerializer(art).data


def _latest_run(project) -> V3CommandRun | None:
    return (
        V3CommandRun.objects.filter(
            project=project, command_type__in=_DELIVERY_RUN_COMMANDS
        )
        .order_by("-created_at")
        .first()
    )


def _delivery_state(project) -> dict:
    package = latest(
        project, _PACKAGE_KEY, status=V3ArtifactVersion.Status.COMMITTED
    )
    run = _latest_run(project)
    return {
        "stage": project.stage,
        "gate": evaluate_delivery_gate(project),
        "package": _serialize_artifact(package),
        "latest_run": CommandRunSerializer(run).data if run is not None else None,
    }


class V3DeliveryStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        return api_response(_delivery_state(project))


class V3DeliveryPrepareView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        run = dispatch_command(
            owner=request.user,
            command_type="prepare_delivery",
            payload={"project_id": str(project.id)},
        )
        return api_response({"command_run": CommandRunSerializer(run).data})


class V3DeliveryExportDocxView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id):
        project = _owned_v3_project(request, project_id)
        gate = evaluate_delivery_gate(project)
        if not gate.get("passed"):
            blockers = gate.get("blockers") or []
            return api_error(
                400,
                "交付门禁未通过",
                data={"passed": False, "blockers": blockers},
            )

        scripts = latest(
            project, _SCRIPTS_KEY, status=V3ArtifactVersion.Status.COMMITTED
        )
        payload = (
            scripts.payload
            if scripts is not None and isinstance(scripts.payload, dict)
            else {}
        )
        content = build_episode_scripts_docx(
            project_title=project.title,
            scripts_payload=payload,
        )
        filename = _docx_filename(project.title)
        return FileResponse(
            BytesIO(content),
            as_attachment=True,
            filename=filename,
            content_type=_DOCX_CONTENT_TYPE,
        )


def _docx_filename(title: str) -> str:
    raw = (title or "").strip() or "script"
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", " ") else "_" for ch in raw)
    safe = safe.strip() or "script"
    return f"{safe}.docx"
