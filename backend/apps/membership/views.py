"""
会员模块 API 视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import MembershipPlan, UserMembership
from .serializers import (
    MembershipPlanSerializer,
    UserMembershipSerializer,
    UserMembershipSummarySerializer,
    RedeemPromoCodeSerializer,
    RedeemPromoCodeResultSerializer,
)
from .services import MembershipService


class MembershipPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """会员套餐：只读列表/详情"""

    queryset = MembershipPlan.objects.filter(is_active=True).order_by(
        "sort_order", "-created_at"
    )
    serializer_class = MembershipPlanSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class MyMembershipView(APIView):
    """我的会员：当前有效会员信息"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = MembershipService.get_current_membership(request.user)
        if not membership:
            return Response({"detail": "暂无有效会员"}, status=status.HTTP_200_OK)
        serializer = UserMembershipSerializer(membership)
        return Response(serializer.data)


class MembershipSummaryView(APIView):
    """会员状态摘要（简洁版）"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        summary = MembershipService.get_membership_summary(request.user)
        serializer = UserMembershipSummarySerializer(summary)
        return Response(serializer.data)


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
        return Response(serializer.data)


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
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)
