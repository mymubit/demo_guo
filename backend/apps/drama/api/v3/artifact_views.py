# -*- coding: utf-8 -*-
"""V3 产物版本列表与回滚 API。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_error, api_response
from apps.drama.api.v3.serializers import (
    ArtifactRollbackSerializer,
    ArtifactVersionSerializer,
)
from apps.drama.api.v3.views import _owned_v3_project
from apps.drama.orchestrator.artifact_rollback import (
    ArtifactRollbackError,
    list_committed_versions,
    rollback_artifact,
)


class V3ArtifactListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        artifact_key = (request.query_params.get("artifact_key") or "").strip()
        if not artifact_key:
            return api_error(400, "缺少 artifact_key 查询参数")
        try:
            items = list_committed_versions(project, artifact_key)
        except ArtifactRollbackError as exc:
            return api_error(400, str(exc))
        return api_response(
            {"items": ArtifactVersionSerializer(items, many=True).data}
        )


class V3ArtifactRollbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, project_id) -> Response:
        project = _owned_v3_project(request, project_id)
        serializer = ArtifactRollbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        actor = getattr(request.user, "username", None) or str(
            getattr(request.user, "pk", "system")
        )
        try:
            art = rollback_artifact(
                project=project,
                artifact_key=data["artifact_key"],
                source_version=data["source_version"],
                actor=actor,
            )
        except ArtifactRollbackError as exc:
            return api_error(400, str(exc))
        return api_response(ArtifactVersionSerializer(art).data)
