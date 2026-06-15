"""
会员模块 API 视图
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.membership.models import MembershipPlan, UserMembership
from apps.membership.feature_matrix import build_feature_matrix_payload
from apps.membership.serializers import (
    MembershipPlanSerializer,
    UserMembershipSerializer,
    UserMembershipSummarySerializer,
    RedeemPromoCodeSerializer,
)
from apps.membership.services import MembershipService


class MembershipPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """会员套餐：只读列表/详情"""

    queryset = MembershipPlan.objects.filter(is_active=True).order_by(
        "sort_order", "-created_at"
    )
    serializer_class = MembershipPlanSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"code": 0, "message": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"code": 0, "message": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class MyMembershipView(APIView):
    """我的会员：当前有效会员信息"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = MembershipService.get_current_membership(request.user)
        if not membership:
            return Response(
                {"code": 0, "message": "success", "data": None},
                status=status.HTTP_200_OK,
            )
        serializer = UserMembershipSerializer(membership)
        return Response(
            {"code": 0, "message": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class MembershipSummaryView(APIView):
    """会员状态摘要（简洁版）"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        summary = MembershipService.get_membership_summary(request.user)
        serializer = UserMembershipSummarySerializer(summary)
        return Response(
            {"code": 0, "message": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class FeatureMatrixView(APIView):
    """GET /api/members/feature-matrix/ — 免费 vs 会员权益对比"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = build_feature_matrix_payload(request.user)
        return Response(
            {"code": 0, "message": "success", "data": data},
            status=status.HTTP_200_OK,
        )


class MyMembershipHistoryView(APIView):
    """我的会员历史记录"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            UserMembership.objects.filter(user=request.user)
            .select_related("plan")
            .order_by("-created_at")
        )
        serializer = UserMembershipSerializer(queryset, many=True)
        return Response(
            {"code": 0, "message": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class RedeemPromoCodeView(APIView):
    """卡密兑换会员"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RedeemPromoCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]

        success, message, user_membership, plan = MembershipService.redeem_promo_code(
            request.user, code
        )

        result = {
            "success": success,
            "message": message,
            "plan": MembershipPlanSerializer(plan).data if plan else None,
            "user_membership": (
                UserMembershipSerializer(user_membership).data
                if user_membership
                else None
            ),
        }

        if not success:
            return Response(
                {"code": 4001, "message": message, "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "兑换成功", "data": result},
            status=status.HTTP_200_OK,
        )
