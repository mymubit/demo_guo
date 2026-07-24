# -*- coding: utf-8 -*-
"""旧 /api/v2 统一下线：410 Gone。"""
from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response

V2_GONE_MESSAGE = "旧接口已下线，请使用 /api/v3/"


class V2GoneView(APIView):
    """所有 /api/v2/** 返回 410，引导使用 /api/v3/。"""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def _gone(self, request: Request, rest: str | None = None) -> Response:
        return api_response(
            data=None,
            code=410,
            message=V2_GONE_MESSAGE,
            status=410,
        )

    def get(self, request: Request, rest: str | None = None) -> Response:
        return self._gone(request, rest)

    def post(self, request: Request, rest: str | None = None) -> Response:
        return self._gone(request, rest)

    def put(self, request: Request, rest: str | None = None) -> Response:
        return self._gone(request, rest)

    def patch(self, request: Request, rest: str | None = None) -> Response:
        return self._gone(request, rest)

    def delete(self, request: Request, rest: str | None = None) -> Response:
        return self._gone(request, rest)
