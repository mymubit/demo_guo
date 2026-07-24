# -*- coding: utf-8 -*-
"""V3 模板库 REST。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.serializers import (
    CustomTemplatePatchSerializer,
    CustomTemplateWriteSerializer,
)
from apps.drama.permissions import DramaConfigWritePermission
from apps.drama.services.templates_service import (
    create_custom_template,
    delete_custom_template,
    list_templates,
    update_custom_template,
)


class V3TemplateListView(APIView):
    """GET /api/v3/templates/ — 内置 + 自定义（登录可读）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return api_response(list_templates())


class V3TemplateCustomCreateView(APIView):
    """POST /api/v3/templates/custom/ — staff 创建。"""

    permission_classes = [DramaConfigWritePermission]

    def post(self, request: Request) -> Response:
        serializer = CustomTemplateWriteSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = create_custom_template(
            data=dict(serializer.validated_data), user=request.user
        )
        return api_response(data)


class V3TemplateCustomDetailView(APIView):
    """PATCH/DELETE /api/v3/templates/custom/{id}/ — staff。"""

    permission_classes = [DramaConfigWritePermission]

    def patch(self, request: Request, template_id) -> Response:
        serializer = CustomTemplatePatchSerializer(
            data=request.data or {}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        data = update_custom_template(
            template_id=template_id, data=dict(serializer.validated_data)
        )
        return api_response(data)

    def delete(self, request: Request, template_id) -> Response:
        delete_custom_template(template_id=template_id)
        return api_response(None)
