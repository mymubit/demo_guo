# -*- coding: utf-8 -*-
"""V3 系统配置 REST（全局，无 owner FK）。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.serializers import SystemConfigPutSerializer
from apps.drama.orchestrator.system_config import (
    resolve_system_config,
    save_system_overlay,
)


class V3SystemConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return api_response(resolve_system_config())

    def put(self, request: Request) -> Response:
        serializer = SystemConfigPutSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        actor = getattr(request.user, "username", None) or str(request.user.pk)
        state = save_system_overlay(
            overlay=data["overlay"],
            actor=actor,
            change_reason=data.get("change_reason") or "",
        )
        return api_response(state)
