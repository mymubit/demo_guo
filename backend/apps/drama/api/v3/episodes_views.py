# -*- coding: utf-8 -*-
"""V3 分集 Episodes REST API。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.serializers import (
    ArtifactVersionSerializer,
    CommandRunSerializer,
    EpisodeGenerateSerializer,
    EpisodeReviseSerializer,
)
from apps.drama.api.v3.views import _owned_v3_project
from apps.drama.models import V3ArtifactVersion, V3CommandRun
from apps.drama.orchestrator import dispatch_command
from apps.drama.orchestrator.artifacts import latest

_EPISODE_KEY = "episode_plan"
_EPISODE_COMMANDS = (
    "generate_episode_plan",
    "revise_episode_plan",
    "confirm_episode_plan",
)


def _serialize_artifact(art: V3ArtifactVersion | None) -> dict | None:
    if art is None:
        return None
    return ArtifactVersionSerializer(art).data


def _latest_episode_run(project) -> V3CommandRun | None:
    return (
        V3CommandRun.objects.filter(
            project=project, command_type__in=_EPISODE_COMMANDS
        )
        .order_by("-created_at")
        .first()
    )


def _episodes_state(project) -> dict:
    run = _latest_episode_run(project)
    return {
        "stage": project.stage,
        "committed": _serialize_artifact(
            latest(project, _EPISODE_KEY, status=V3ArtifactVersion.Status.COMMITTED)
        ),
        "candidate": _serialize_artifact(
            latest(project, _EPISODE_KEY, status=V3ArtifactVersion.Status.CANDIDATE)
        ),
        "latest_run": CommandRunSerializer(run).data if run is not None else None,
    }


class V3EpisodesStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        return api_response(_episodes_state(project))


class V3EpisodesGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = EpisodeGenerateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        payload = {"project_id": str(project.id)}
        for key in ("episode_count", "duration_target", "planning_requests"):
            if key in serializer.validated_data:
                payload[key] = serializer.validated_data[key]
        run = dispatch_command(
            owner=request.user,
            command_type="generate_episode_plan",
            payload=payload,
        )
        return api_response({"command_run": CommandRunSerializer(run).data})


class V3EpisodesConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        run = dispatch_command(
            owner=request.user,
            command_type="confirm_episode_plan",
            payload={"project_id": str(project.id)},
        )
        return api_response({"command_run": CommandRunSerializer(run).data})


class V3EpisodesReviseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = EpisodeReviseSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        payload = {
            "project_id": str(project.id),
            "episode_numbers": serializer.validated_data["episode_numbers"],
        }
        if "revision_requests" in serializer.validated_data:
            payload["revision_requests"] = serializer.validated_data[
                "revision_requests"
            ]
        run = dispatch_command(
            owner=request.user,
            command_type="revise_episode_plan",
            payload=payload,
        )
        return api_response({"command_run": CommandRunSerializer(run).data})
