# -*- coding: utf-8 -*-
"""V3 模型单价 REST。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.models_service import V3ModelsService
from apps.drama.api.v3.serializers import ModelPriceTableSerializer


class V3ModelPricesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return api_response(V3ModelsService.list_prices())

    def put(self, request: Request) -> Response:
        serializer = ModelPriceTableSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = V3ModelsService.put_prices(
            list(serializer.validated_data["items"])
        )
        return api_response(data)


class V3ModelPriceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, price_id: int) -> Response:
        return api_response(V3ModelsService.delete_price(price_id))
