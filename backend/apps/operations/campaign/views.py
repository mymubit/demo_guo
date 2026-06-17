"""运营活动 API。"""
from __future__ import annotations

import logging
from datetime import datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.operations.campaign import services
from apps.operations.campaign.models import (
    Campaign,
    CouponClaimLog,
    CouponTemplate,
    RedemptionCode,
    RedemptionCodeBatch,
    UserCoupon,
)
from apps.operations.campaign.serializers import (
    CampaignSerializer,
    CouponClaimLogSerializer,
    CouponTemplateSerializer,
    RedemptionCodeBatchSerializer,
    RedemptionCodeSerializer,
    UserCouponSerializer,
)
from apps.operations.exceptions import OperationsError
from apps.operations.permissions import DOMAIN_COMMERCE, DOMAIN_GROWTH, HasOpsDomain

logger = logging.getLogger(__name__)


def _parse_dt(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        # 前端可发 ISO 8601；兼容 "Z" 后缀
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


class CampaignViewSet(ModelViewSet):
    """活动管理。"""

    queryset = Campaign.objects.all().order_by("-start_at")
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_COMMERCE
    search_fields = ["name", "slug"]
    filterset_fields = ["campaign_type", "status"]

    def perform_create(self, serializer):
        serializer.save(created_by=getattr(self.request.user, "username", ""))

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        try:
            campaign = services.activate_campaign(
                int(pk), operator=getattr(request.user, "username", ""),
            )
        except Campaign.DoesNotExist:
            return api_fail("活动不存在", code=404, http_status=status.HTTP_404_NOT_FOUND)
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(CampaignSerializer(campaign).data, message="活动已启动")

    @action(detail=True, methods=["post"], url_path="pause")
    def pause(self, request, pk=None):
        try:
            campaign = services.pause_campaign(
                int(pk), operator=getattr(request.user, "username", ""),
            )
        except Campaign.DoesNotExist:
            return api_fail("活动不存在", code=404, http_status=status.HTTP_404_NOT_FOUND)
        return api_ok(CampaignSerializer(campaign).data, message="活动已暂停")

    @action(detail=True, methods=["post"], url_path="end")
    def end(self, request, pk=None):
        try:
            campaign = services.end_campaign(
                int(pk), operator=getattr(request.user, "username", ""),
            )
        except Campaign.DoesNotExist:
            return api_fail("活动不存在", code=404, http_status=status.HTTP_404_NOT_FOUND)
        return api_ok(CampaignSerializer(campaign).data, message="活动已结束")

    @action(detail=False, methods=["get"], url_path="active")
    def active(self, request):
        now = timezone.now()
        rows = Campaign.objects.filter(
            status="running", start_at__lte=now, end_at__gte=now,
        ).order_by("-start_at")
        return api_ok(CampaignSerializer(rows, many=True).data)


class CouponTemplateViewSet(ModelViewSet):
    """卡券模板管理。"""

    queryset = CouponTemplate.objects.all().order_by("-created_at")
    serializer_class = CouponTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_COMMERCE
    search_fields = ["name"]
    filterset_fields = ["coupon_type", "status", "campaign"]


class RedemptionCodeBatchViewSet(ModelViewSet):
    """兑换码批次管理。"""

    queryset = RedemptionCodeBatch.objects.all().order_by("-created_at")
    serializer_class = RedemptionCodeBatchSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_COMMERCE
    filterset_fields = ["template", "campaign"]

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        data = request.data or {}
        try:
            template_id = int(data.get("template_id", 0))
            count = int(data.get("count", 0))
        except (TypeError, ValueError):
            return api_fail("参数错误", code=400)
        if template_id <= 0 or count <= 0:
            return api_fail("template_id 与 count 必填", code=400)
        try:
            batch = services.generate_redemption_codes(
                template_id=template_id,
                count=count,
                operator=getattr(request.user, "username", ""),
                name=str(data.get("name", ""))[:128],
                prefix=str(data.get("prefix", ""))[:8],
                code_length=int(data.get("code_length", 12)),
                campaign_id=data.get("campaign_id") or None,
                expires_at=_parse_dt(data.get("expires_at", "")),
            )
        except CouponTemplate.DoesNotExist:
            return api_fail("卡券模板不存在", code=404, http_status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return api_fail(str(e), code=400)
        return api_ok(RedemptionCodeBatchSerializer(batch).data, message="兑换码已生成")


class RedemptionCodeViewSet(ReadOnlyModelViewSet):
    """兑换码查询（运营只读，禁用/导出）。"""

    queryset = RedemptionCode.objects.all().order_by("-created_at")
    serializer_class = RedemptionCodeSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_COMMERCE
    filterset_fields = ["batch", "status"]

    @action(detail=True, methods=["post"], url_path="disable")
    def disable(self, request, pk=None):
        rc = self.get_object()
        from apps.operations.constants import RedemptionCodeStatus
        rc.status = RedemptionCodeStatus.DISABLED
        rc.save(update_fields=["status", "updated_at"])
        return api_ok(RedemptionCodeSerializer(rc).data, message="兑换码已作废")

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        """导出未领取的码值（CSV）。"""
        import csv

        from django.http import HttpResponse

        batch_id = request.query_params.get("batch")
        qs = self.get_queryset().filter(status="unclaimed")
        if batch_id:
            qs = qs.filter(batch_id=batch_id)
        qs = qs.values_list("code", flat=True)[:50000]
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="redemption_codes.csv"'
        writer = csv.writer(resp)
        writer.writerow(["code"])
        for code in qs:
            writer.writerow([code])
        return resp


class UserCouponClaimView(GenericAPIView):
    """用户端：C 端用户领取卡券/兑换码。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data or {}
        try:
            coupon = services.claim_coupon(
                user=request.user,
                campaign_id=data.get("campaign_id"),
                template_id=data.get("template_id"),
                claim_source=str(data.get("source", "campaign")),
                redemption_code=str(data.get("redemption_code", "")),
                ip=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(UserCouponSerializer(coupon).data, message="领取成功")


class UserCouponListView(GenericAPIView):
    """用户端：我的卡券列表。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        include_expired = request.query_params.get("include_expired") in ("1", "true")
        coupons = services.get_user_coupons(request.user, include_expired=include_expired)
        return api_ok(UserCouponSerializer(coupons, many=True).data)


class CouponClaimLogViewSet(ReadOnlyModelViewSet):
    """领取审计日志查询。"""

    queryset = CouponClaimLog.objects.all().order_by("-created_at")
    serializer_class = CouponClaimLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_COMMERCE
    filterset_fields = ["campaign", "template", "result", "claim_source"]
