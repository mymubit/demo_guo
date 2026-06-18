# -*- coding: utf-8 -*-
"""批量创作 API（已废弃）。"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail

_GONE_MESSAGE = "批量创作 API 已移除。"


def _legacy_removed_response():
    return api_fail(_GONE_MESSAGE, code=410)


class BatchJobListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return _legacy_removed_response()


class BatchJobCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        return _legacy_removed_response()


class BatchJobDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, batch_id: str):
        return _legacy_removed_response()


class BatchJobDispatchView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, batch_id: str):
        return _legacy_removed_response()


class BatchJobPauseView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, batch_id: str):
        return _legacy_removed_response()


class BatchJobResumeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, batch_id: str):
        return _legacy_removed_response()


class BatchProjectRetryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, batch_id: str, project_id: str):
        return _legacy_removed_response()
