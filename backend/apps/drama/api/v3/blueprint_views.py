# -*- coding: utf-8 -*-
"""V3 蓝图 Blueprint REST API。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.serializers import (
    ArtifactVersionSerializer,
    BlueprintConfirmSerializer,
    CommandRunSerializer,
)
from apps.drama.api.v3.views import _owned_v3_project
from apps.drama.models import V3ArtifactVersion, V3CommandRun
from apps.drama.orchestrator import dispatch_command
from apps.drama.orchestrator.artifacts import latest
from apps.drama.skills_bridge.recipe_map import recipe_for

_BLUEPRINT_KEYS = tuple(recipe_for("generate_blueprint")["writes"])
_BLUEPRINT_COMMANDS = ("generate_blueprint", "confirm_blueprint")


def _bundle_by_status(project, status: str) -> dict | None:
    items: dict[str, dict] = {}
    for key in _BLUEPRINT_KEYS:
        art = latest(project, key, status=status)
        if art is not None:
            items[key] = ArtifactVersionSerializer(art).data
    return items or None


def _latest_blueprint_run(project) -> V3CommandRun | None:
    return (
        V3CommandRun.objects.filter(
            project=project, command_type__in=_BLUEPRINT_COMMANDS
        )
        .order_by("-created_at")
        .first()
    )


def _blueprint_state(project) -> dict:
    run = _latest_blueprint_run(project)
    return {
        "committed": _bundle_by_status(project, V3ArtifactVersion.Status.COMMITTED),
        "candidate": _bundle_by_status(project, V3ArtifactVersion.Status.CANDIDATE),
        "latest_run": CommandRunSerializer(run).data if run is not None else None,
    }


class V3BlueprintStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        return api_response(_blueprint_state(project))


class V3BlueprintGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        run = dispatch_command(
            owner=request.user,
            command_type="generate_blueprint",
            payload={"project_id": str(project.id)},
        )
        return api_response({"command_run": CommandRunSerializer(run).data})


class V3BlueprintConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = BlueprintConfirmSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        run = dispatch_command(
            owner=request.user,
            command_type="confirm_blueprint",
            payload={"project_id": str(project.id)},
        )
        return api_response({"command_run": CommandRunSerializer(run).data})
