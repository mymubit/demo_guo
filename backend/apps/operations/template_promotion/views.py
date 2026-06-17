"""模板沉淀 API。"""
from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.operations.exceptions import OperationsError
from apps.operations.permissions import DOMAIN_CONTENT, HasOpsDomain
from apps.operations.template_promotion import services
from apps.operations.template_promotion.models import TemplatePromotion
from apps.operations.template_promotion.serializers import (
    TemplatePromotionSerializer,
)

logger = logging.getLogger(__name__)


class TemplatePromotionViewSet(ModelViewSet):
    """爆款模板沉淀管理。"""

    queryset = TemplatePromotion.objects.all().order_by("-created_at")
    serializer_class = TemplatePromotionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT
    search_fields = ["name", "description", "category"]
    filterset_fields = ["status", "category"]

    def perform_create(self, serializer):
        serializer.save(created_by=getattr(self.request.user, "username", ""))

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        p = self.get_object()
        try:
            p = services.transition(
                p,
                to_status=request.data.get("status", ""),
                operator=getattr(request.user, "username", ""),
                note=str(request.data.get("note", ""))[:1000],
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(TemplatePromotionSerializer(p).data, message="状态已变更")
