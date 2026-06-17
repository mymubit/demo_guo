"""A/B 实验 API。"""
from __future__ import annotations

import logging

from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.operations.exceptions import OperationsError
from apps.operations.experiment import services
from apps.operations.experiment.models import (
    Assignment,
    ConversionLog,
    Experiment,
    ExperimentMetricSnapshot,
    ExposureLog,
    Variant,
)
from apps.operations.experiment.serializers import (
    AssignmentSerializer,
    ConversionLogSerializer,
    ExperimentMetricSnapshotSerializer,
    ExperimentSerializer,
    ExposureLogSerializer,
    VariantSerializer,
)
from apps.operations.permissions import DOMAIN_EXPERIMENT, HasOpsDomain

logger = logging.getLogger(__name__)


class ExperimentViewSet(ModelViewSet):
    """实验管理。"""

    queryset = Experiment.objects.all().prefetch_related("variants").order_by("-created_at")
    serializer_class = ExperimentSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_EXPERIMENT
    search_fields = ["name", "key", "description"]
    filterset_fields = ["status", "bucket"]

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        exp = self.get_object()
        try:
            exp = services.start_experiment(exp, operator=getattr(request.user, "username", ""))
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(ExperimentSerializer(exp).data, message="实验已启动")

    @action(detail=True, methods=["post"], url_path="pause")
    def pause(self, request, pk=None):
        exp = self.get_object()
        try:
            exp = services.pause_experiment(exp, operator=getattr(request.user, "username", ""))
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(ExperimentSerializer(exp).data, message="实验已暂停")

    @action(detail=True, methods=["post"], url_path="conclude")
    def conclude(self, request, pk=None):
        exp = self.get_object()
        try:
            exp = services.conclude_experiment(
                exp,
                winner_variant_key=str(request.data.get("winner_variant", ""))[:64],
                conclusion=str(request.data.get("conclusion", ""))[:1000],
                operator=getattr(request.user, "username", ""),
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(ExperimentSerializer(exp).data, message="实验已结束")

    @action(detail=True, methods=["get"], url_path="analyze")
    def analyze(self, request, pk=None):
        exp = self.get_object()
        return api_ok(services.analyze_experiment(exp))

    @action(detail=True, methods=["post"], url_path="snapshot")
    def snapshot(self, request, pk=None):
        exp = self.get_object()
        try:
            rows = services.build_daily_snapshot(exp.id)
        except Experiment.DoesNotExist:
            return api_fail("实验不存在", code=404, http_status=status.HTTP_404_NOT_FOUND)
        return api_ok({"snapshot_rows": rows}, message="快照已构建")


class VariantViewSet(ModelViewSet):
    """变体管理。"""

    queryset = Variant.objects.all().order_by("experiment_id", "sort_order", "id")
    serializer_class = VariantSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_EXPERIMENT
    filterset_fields = ["experiment", "is_control"]


class AssignmentViewSet(ReadOnlyModelViewSet):
    """分配记录查询。"""

    queryset = Assignment.objects.all().order_by("-assigned_at")
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_EXPERIMENT
    filterset_fields = ["experiment", "variant_key", "user"]


class ExposureLogViewSet(ReadOnlyModelViewSet):
    """曝光日志查询。"""

    queryset = ExposureLog.objects.all().order_by("-created_at")
    serializer_class = ExposureLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_EXPERIMENT
    filterset_fields = ["experiment", "variant", "surface"]


class ConversionLogViewSet(ReadOnlyModelViewSet):
    """转化日志查询。"""

    queryset = ConversionLog.objects.all().order_by("-created_at")
    serializer_class = ConversionLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_EXPERIMENT
    filterset_fields = ["experiment", "variant", "metric"]


class ExperimentMetricSnapshotViewSet(ReadOnlyModelViewSet):
    """实验指标快照。"""

    queryset = ExperimentMetricSnapshot.objects.all().order_by("-snapshot_date")
    serializer_class = ExperimentMetricSnapshotSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_EXPERIMENT
    filterset_fields = ["experiment", "variant", "metric", "snapshot_date"]


# ──────────────────────────────────────────────
# C 端：分配 + 埋点
# ──────────────────────────────────────────────
class ClientAssignView(GenericAPIView):
    """C 端：客户端启动时批量获取进入的实验变体。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        keys = request.data.get("keys") or []
        if not isinstance(keys, list):
            return api_fail("keys 必须为数组", code=400)
        result = {}
        for key in keys[:32]:
            try:
                exp = Experiment.objects.get(key=str(key))
            except Experiment.DoesNotExist:
                result[str(key)] = None
                continue
            variant = services.assign_variant(
                exp, user=request.user, anonymous_id=str(request.data.get("anonymous_id", "")),
            )
            if variant is None:
                result[str(key)] = None
            else:
                result[str(key)] = {
                    "variant_key": variant.key,
                    "payload": variant.payload,
                }
        return api_ok({"assignments": result})


class ClientEventView(GenericAPIView):
    """C 端：客户端埋点（曝光 / 转化）。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        kind = str(request.data.get("type", "exposure"))
        experiment_key = str(request.data.get("experiment_key", ""))
        variant_key = str(request.data.get("variant_key", ""))
        if not experiment_key or not variant_key:
            return api_fail("缺少 experiment_key / variant_key", code=400)
        surface = str(request.data.get("surface", ""))[:64]
        context = request.data.get("context") or {}
        anonymous_id = str(request.data.get("anonymous_id", ""))[:64]

        if kind == "exposure":
            ok = services.log_exposure(
                experiment_key=experiment_key, variant_key=variant_key,
                user=request.user, anonymous_id=anonymous_id,
                surface=surface, context=context,
            )
        elif kind == "conversion":
            try:
                value = float(request.data.get("value", 1))
            except (TypeError, ValueError):
                value = 1.0
            metric = str(request.data.get("metric", "primary"))[:64]
            ok = services.log_conversion(
                experiment_key=experiment_key, variant_key=variant_key,
                metric=metric, value=value,
                user=request.user, anonymous_id=anonymous_id, surface=surface,
            )
        else:
            return api_fail("type 仅支持 exposure / conversion", code=400)
        if not ok:
            return api_fail("实验或变体不存在", code=404, http_status=status.HTTP_404_NOT_FOUND)
        return api_ok(message="已记录")
