"""运营数据看板 API。"""
from __future__ import annotations

import logging

from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_ok
from apps.operations.analytics import services
from apps.operations.permissions import DOMAIN_DATA, HasOpsDomain

logger = logging.getLogger(__name__)


class _OpsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_DATA


class CoreOverviewView(_OpsView):
    def get(self, request):
        return api_ok(services.core_overview(request.query_params))


class UserAnalyticsView(_OpsView):
    def get(self, request):
        return api_ok(services.user_analytics(request.query_params))


class CreationAnalyticsView(_OpsView):
    def get(self, request):
        return api_ok(services.creation_analytics(request.query_params))


class ConversionAnalyticsView(_OpsView):
    def get(self, request):
        return api_ok(services.conversion_analytics(request.query_params))


class FeatureUsageAnalyticsView(_OpsView):
    def get(self, request):
        return api_ok(services.feature_usage_analytics(request.query_params))
