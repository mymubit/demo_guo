# -*- coding: utf-8 -*-
"""V3 正文 Scripts REST API（含按集草稿）。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.serializers import (
    ArtifactVersionSerializer,
    CommandRunSerializer,
    ScriptConfirmSerializer,
    ScriptDraftPutSerializer,
    ScriptGenerateSerializer,
)
from apps.drama.api.v3.views import _owned_v3_project
from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3ScriptDraft
from apps.drama.orchestrator import dispatch_command
from apps.drama.orchestrator.artifacts import latest

_SCRIPT_KEY = "episode_scripts"
_SCRIPT_COMMANDS = ("write_episode_batch", "confirm_script_candidate")


def _serialize_artifact(art: V3ArtifactVersion | None) -> dict | None:
    if art is None:
        return None
    return ArtifactVersionSerializer(art).data


def _serialize_draft(draft: V3ScriptDraft) -> dict:
    return {
        "episode_number": draft.episode_number,
        "payload": draft.payload,
        "updated_at": draft.updated_at.isoformat().replace("+00:00", "Z")
        if draft.updated_at
        else None,
    }


def _latest_script_run(project) -> V3CommandRun | None:
    return (
        V3CommandRun.objects.filter(
            project=project, command_type__in=_SCRIPT_COMMANDS
        )
        .order_by("-created_at")
        .first()
    )


def _episode_slice(art: V3ArtifactVersion | None, episode_number: int) -> dict | None:
    if art is None:
        return None
    episodes = (art.payload or {}).get("episodes") or []
    for ep in episodes:
        if isinstance(ep, dict) and ep.get("episode_number") == episode_number:
            return ep
    return None


def _scripts_state(project) -> dict:
    run = _latest_script_run(project)
    drafts = [
        _serialize_draft(d)
        for d in V3ScriptDraft.objects.filter(project=project).order_by(
            "episode_number"
        )
    ]
    return {
        "committed": _serialize_artifact(
            latest(project, _SCRIPT_KEY, status=V3ArtifactVersion.Status.COMMITTED)
        ),
        "candidate": _serialize_artifact(
            latest(project, _SCRIPT_KEY, status=V3ArtifactVersion.Status.CANDIDATE)
        ),
        "drafts": drafts,
        "latest_run": CommandRunSerializer(run).data if run is not None else None,
    }


class V3ScriptsStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        return api_response(_scripts_state(project))


class V3ScriptEpisodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id, episode_number: int) -> Response:
        project = _owned_v3_project(request, project_id)
        committed = latest(
            project, _SCRIPT_KEY, status=V3ArtifactVersion.Status.COMMITTED
        )
        candidate = latest(
            project, _SCRIPT_KEY, status=V3ArtifactVersion.Status.CANDIDATE
        )
        draft = V3ScriptDraft.objects.filter(
            project=project, episode_number=episode_number
        ).first()
        return api_response(
            {
                "episode_number": episode_number,
                "committed": _episode_slice(committed, episode_number),
                "candidate": _episode_slice(candidate, episode_number),
                "draft": _serialize_draft(draft) if draft is not None else None,
            }
        )


class V3ScriptDraftView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request: Request, project_id, episode_number: int) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = ScriptDraftPutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        draft, _created = V3ScriptDraft.objects.update_or_create(
            project=project,
            episode_number=episode_number,
            defaults={"payload": serializer.validated_data["payload"]},
        )
        return api_response(_serialize_draft(draft))


class V3ScriptsGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = ScriptGenerateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        payload = {
            "project_id": str(project.id),
            "episode_range": {
                "start": serializer.validated_data["start"],
                "end": serializer.validated_data["end"],
            },
        }
        if "writing_requests" in serializer.validated_data:
            payload["writing_requests"] = serializer.validated_data["writing_requests"]
        run = dispatch_command(
            owner=request.user,
            command_type="write_episode_batch",
            payload=payload,
        )
        return api_response({"command_run": CommandRunSerializer(run).data})


class V3ScriptsConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = ScriptConfirmSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        payload = {
            "project_id": str(project.id),
            "use_drafts": serializer.validated_data.get("use_drafts", False),
        }
        run = dispatch_command(
            owner=request.user,
            command_type="confirm_script_candidate",
            payload=payload,
        )
        return api_response({"command_run": CommandRunSerializer(run).data})
