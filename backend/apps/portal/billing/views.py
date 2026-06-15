# -*- coding: utf-8 -*-
from decimal import Decimal

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import PermissionDenied

from apps.billing.commerce_pricing import discount_display_label, normalize_discount_percent, quantize_yuan
from apps.billing.models import RechargePackage
from apps.billing.services import BillingService
from apps.workflow.services.pipeline_service import WorkflowPipelineService
from apps.orders.services import OrderService, PaymentService
from .serializers import RechargeOrderCreateSerializer


def _serialize_package(pkg: RechargePackage, user) -> dict:
    from apps.billing.recharge_grant import resolve_recharge_grant_coins

    grant = resolve_recharge_grant_coins(pkg, user)
    total = grant["total_coins"]
    charge = pkg.charge_price
    unit = float(charge) / total if total else 0
    original = pkg.original_price_yuan
    if original is None and pkg.discount_percent and charge > 0:
        discount = normalize_discount_percent(pkg.discount_percent)
        if discount < Decimal("100"):
            original = quantize_yuan(charge * Decimal("100") / discount)
    bonus = grant["bonus_coins"]
    configured_bonus = grant["configured_bonus_coins"]
    return {
        "id": str(pkg.id),
        "name": pkg.name,
        "price_yuan": str(charge),
        "original_price_yuan": str(original) if original else None,
        "discount_percent": str(pkg.discount_percent),
        "discount_label": discount_display_label(pkg.discount_percent),
        "base_coins": grant["base_coins"],
        "bonus_coins": bonus,
        "configured_bonus_coins": configured_bonus,
        "member_bonus_eligible": grant["member_bonus_eligible"],
        "bonus_coins_text": f"额外赠送 {bonus} 创作币" if bonus > 0 else None,
        "member_bonus_hint": (
            f"开通会员后可额外获赠 {configured_bonus} 创作币"
            if not grant["member_bonus_eligible"] and configured_bonus > 0
            else None
        ),
        "total_coins": total,
        "unit_price": round(unit, 4),
        "sort_order": pkg.sort_order,
    }


class WalletView(APIView):
    """GET /api/billing/wallet/ — 用户币种余额"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = BillingService.get_wallet_summary(request.user)
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class BillingCatalogView(APIView):
    """GET /api/billing/catalog/ — 公开定价与主链节点（仅名称+币价）"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.orders.payment_provider import PaymentProvider

        data = {
            "currency_name": BillingService.currency_name(),
            "balance": BillingService.get_balance(request.user),
            "submit_cost": BillingService.get_price("creation.submit"),
            "estimated_auto_cost": BillingService.estimate_auto_pipeline_cost(),
            "pipeline_nodes": WorkflowPipelineService.public_nodes(),
            "pricing": BillingService.list_active_pricing(),
            "field_actions": BillingService.list_field_actions(),
            "payment_method": PaymentProvider.resolve_method(None),
        }
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class RechargePackageListView(APIView):
    """GET /api/billing/recharge/packages/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = RechargePackage.objects.filter(is_active=True).order_by("sort_order", "price_yuan")
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": [_serialize_package(p, request.user) for p in qs],
            },
            status=status.HTTP_200_OK,
        )


class RechargeOrderCreateView(APIView):
    """POST /api/billing/recharge/orders/ body: { package_id, payment_method? }"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RechargeOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.orders.payment_provider import PaymentProvider

        payment_method = PaymentProvider.resolve_method(serializer.validated_data.get("payment_method"))
        order, err = OrderService.create_recharge_order(
            request.user,
            serializer.validated_data["package_id"],
            payment_method=payment_method,
        )
        if err:
            return Response(
                {"code": 4001, "message": err, "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "order_no": order.order_no,
                    "amount": str(order.amount),
                    "coins_granted": order.coins_granted,
                    "order_type": order.order_type,
                    "status": order.status,
                },
            },
            status=status.HTTP_200_OK,
        )


class RechargeOrderMockPayView(APIView):
    """POST /api/billing/recharge/orders/<order_no>/mock_pay/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, order_no: str):
        from apps.orders.models import Order

        order = OrderService.get_order_detail(request.user, order_no)
        if not order:
            return Response(
                {"code": 404, "message": "订单不存在", "data": None},
                status=status.HTTP_200_OK,
            )
        if order.order_type != Order.TYPE_RECHARGE:
            return Response(
                {"code": 4001, "message": "非充值订单", "data": None},
                status=status.HTTP_200_OK,
            )
        try:
            ok, msg, paid_order = PaymentProvider.process_order_payment(order_no, user=request.user)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": str(exc), "data": None},
                status=status.HTTP_200_OK,
            )
        if not ok:
            return Response(
                {"code": 4001, "message": msg, "data": None},
                status=status.HTTP_200_OK,
            )
        wallet = BillingService.get_wallet_summary(request.user)
        return Response(
            {
                "code": 0,
                "message": msg,
                "data": {
                    "order_no": paid_order.order_no,
                    "coins_granted": paid_order.coins_granted,
                    "wallet": wallet,
                },
            },
            status=status.HTTP_200_OK,
        )


class CoinLedgerListView(APIView):
    """GET /api/billing/ledger/?entry_type=income|spend&page=1"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        entry_type = request.query_params.get("entry_type", "")
        page = int(request.query_params.get("page", 1) or 1)
        page_size = int(request.query_params.get("page_size", 20) or 20)
        data = BillingService.list_ledger(
            request.user,
            entry_type=entry_type,
            page=page,
            page_size=page_size,
        )
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": data["items"],
                "pagination": {
                    "total": data["total"],
                    "page": data["page"],
                    "page_size": data["page_size"],
                    "total_pages": data["total_pages"],
                },
            },
            status=status.HTTP_200_OK,
        )
