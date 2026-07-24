# -*- coding: utf-8 -*-
"""V3 选题 Topic REST API。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.serializers import (
    ArtifactVersionSerializer,
    CommandRunSerializer,
    TopicConfirmSerializer,
    TopicDraftPutSerializer,
)
from apps.drama.api.v3.views import _owned_v3_project
from apps.drama.models import V3ArtifactVersion, V3CommandRun
from apps.drama.orchestrator import dispatch_command
from apps.drama.orchestrator.artifacts import latest, next_version

_TOPIC_KEY = "project_brief"
_TOPIC_COMMANDS = ("generate_topic_brief", "confirm_topic_brief")


def _serialize_artifact(art: V3ArtifactVersion | None) -> dict | None:
    if art is None:
        return None
    return ArtifactVersionSerializer(art).data


def _latest_topic_run(project) -> V3CommandRun | None:
    return (
        V3CommandRun.objects.filter(project=project, command_type__in=_TOPIC_COMMANDS)
        .order_by("-created_at")
        .first()
    )


def _topic_state(project) -> dict:
    run = _latest_topic_run(project)
    return {
        "stage": project.stage,
        "committed": _serialize_artifact(
            latest(project, _TOPIC_KEY, status=V3ArtifactVersion.Status.COMMITTED)
        ),
        "candidate": _serialize_artifact(
            latest(project, _TOPIC_KEY, status=V3ArtifactVersion.Status.CANDIDATE)
        ),
        "draft": _serialize_artifact(
            latest(project, _TOPIC_KEY, status=V3ArtifactVersion.Status.DRAFT)
        ),
        "latest_run": CommandRunSerializer(run).data if run is not None else None,
    }


class V3TopicStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        return api_response(_topic_state(project))


class V3TopicDraftView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = TopicDraftPutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data["payload"]
        draft = latest(project, _TOPIC_KEY, status=V3ArtifactVersion.Status.DRAFT)
        if draft is None:
            draft = V3ArtifactVersion.objects.create(
                project=project,
                artifact_key=_TOPIC_KEY,
                version=next_version(project.id, _TOPIC_KEY),
                status=V3ArtifactVersion.Status.DRAFT,
                payload=payload,
            )
        else:
            draft.payload = payload
            draft.save(update_fields=["payload"])
        return api_response(ArtifactVersionSerializer(draft).data)


class V3TopicGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        run = dispatch_command(
            owner=request.user,
            command_type="generate_topic_brief",
            payload={"project_id": str(project.id)},
        )
        return api_response({"command_run": CommandRunSerializer(run).data})


class V3TopicConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = TopicConfirmSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        payload = {
            "project_id": str(project.id),
            "use_draft": serializer.validated_data.get("use_draft", False),
        }
        run = dispatch_command(
            owner=request.user,
            command_type="confirm_topic_brief",
            payload=payload,
        )
        return api_response({"command_run": CommandRunSerializer(run).data})
