# -*- coding: utf-8 -*-
"""V3 模型供应商 / 角色映射 REST。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import VALIDATION_ERROR, BusinessException
from apps.core.responses import api_response
from apps.drama.api.v3.models_service import V3ModelsService
from apps.drama.api.v3.serializers import (
    ModelProviderPatchSerializer,
    ModelProviderWriteSerializer,
    ProviderKeyPatchSerializer,
    ProviderKeyWriteSerializer,
    RoleModelMappingTableSerializer,
)
from apps.drama.orchestrator.provider_test import (
    ProviderTestError,
    test_provider_connectivity,
)


def _actor(request: Request) -> str:
    return getattr(request.user, "username", None) or str(request.user.pk)


class V3ModelProviderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return api_response(V3ModelsService.list_providers())

    def post(self, request: Request) -> Response:
        serializer = ModelProviderWriteSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = V3ModelsService.create_provider(
            dict(serializer.validated_data), actor=_actor(request)
        )
        return api_response(data)


class V3ModelProviderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, provider_id) -> Response:
        return api_response(V3ModelsService.get_provider(provider_id))

    def patch(self, request: Request, provider_id) -> Response:
        serializer = ModelProviderPatchSerializer(
            data=request.data or {}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        data = V3ModelsService.update_provider(
            provider_id, dict(serializer.validated_data), actor=_actor(request)
        )
        return api_response(data)

    def delete(self, request: Request, provider_id) -> Response:
        V3ModelsService.delete_provider(provider_id, actor=_actor(request))
        return api_response(None)


class V3ModelProviderActivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, provider_id) -> Response:
        data = V3ModelsService.activate_provider(
            provider_id, actor=_actor(request)
        )
        return api_response(data)


class V3ModelProviderTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, provider_id) -> Response:
        try:
            data = test_provider_connectivity(
                provider_id=provider_id,
                actor=_actor(request),
            )
        except ProviderTestError as exc:
            raise BusinessException(
                VALIDATION_ERROR,
                str(exc),
                http_status=400,
            ) from exc
        return api_response(data)


class V3ModelProviderKeyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, provider_id) -> Response:
        return api_response(V3ModelsService.list_provider_keys(provider_id))

    def post(self, request: Request, provider_id) -> Response:
        serializer = ProviderKeyWriteSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = V3ModelsService.create_provider_key(
            provider_id,
            dict(serializer.validated_data),
            actor=_actor(request),
        )
        return api_response(data)


class V3ModelProviderKeyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, provider_id, key_id) -> Response:
        serializer = ProviderKeyPatchSerializer(
            data=request.data or {}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        data = V3ModelsService.update_provider_key(
            provider_id,
            key_id,
            dict(serializer.validated_data),
            actor=_actor(request),
        )
        return api_response(data)

    def delete(self, request: Request, provider_id, key_id) -> Response:
        V3ModelsService.delete_provider_key(
            provider_id, key_id, actor=_actor(request)
        )
        return api_response(None)


class V3RoleModelMappingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return api_response(V3ModelsService.list_role_mappings())

    def put(self, request: Request) -> Response:
        serializer = RoleModelMappingTableSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = V3ModelsService.put_role_mappings(
            list(serializer.validated_data["items"])
        )
        return api_response(data)
