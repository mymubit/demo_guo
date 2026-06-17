"""创作者激励 API。"""
from __future__ import annotations

import logging

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.operations.constants import PointsReason
from apps.operations.creator import services
from apps.operations.creator.models import (
    Badge,
    CreatorLevel,
    CreatorProfile,
    PointsAccount,
    PointsTransaction,
)
from apps.operations.creator.serializers import (
    BadgeSerializer,
    CreatorLevelSerializer,
    CreatorProfileSerializer,
    PointsAccountSerializer,
    PointsTransactionSerializer,
)
from apps.operations.exceptions import OperationsError
from apps.operations.permissions import DOMAIN_CONTENT, HasOpsDomain

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 前台：创作者自助
# ──────────────────────────────────────────────

class MyCreatorProfileView(GenericAPIView):
    """我的创作者档案。"""

    permission_classes = [IsAuthenticated]
    serializer_class = CreatorProfileSerializer

    def get(self, request):
        profile = services.get_or_create_profile(request.user)
        return api_ok(CreatorProfileSerializer(profile).data)


class MyPointsAccountView(GenericAPIView):
    """我的积分账户。"""

    permission_classes = [IsAuthenticated]
    serializer_class = PointsAccountSerializer

    def get(self, request):
        account = services.get_points_account(request.user)
        return api_ok(PointsAccountSerializer(account).data)


class MyPointsTransactionsView(ListModelMixin, GenericAPIView):
    """我的积分流水。"""

    permission_classes = [IsAuthenticated]
    serializer_class = PointsTransactionSerializer

    def get(self, request, *args, **kwargs):
        qs = PointsTransaction.objects.filter(user=request.user).order_by("-created_at")
        reason = request.query_params.get("reason")
        if reason:
            qs = qs.filter(reason=reason)
        self.queryset = qs
        return self.list(request, *args, **kwargs)


class MyAchievementsView(GenericAPIView):
    """我的勋章。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.operations.creator.serializers import CreatorAchievementSerializer
        qs = request.user.achievements.select_related("badge").order_by("-unlocked_at")
        return api_ok(CreatorAchievementSerializer(qs, many=True).data)


class LevelListView(GenericAPIView):
    """等级档位列表（前台展示）。"""

    permission_classes = [IsAuthenticated]
    serializer_class = CreatorLevelSerializer

    def get(self, request):
        qs = CreatorLevel.objects.filter(is_active=True).order_by("order", "min_points")
        return api_ok(CreatorLevelSerializer(qs, many=True).data)


# ──────────────────────────────────────────────
# 运营后台
# ──────────────────────────────────────────────

class CreatorLevelAdminViewSet(ModelViewSet):
    queryset = CreatorLevel.objects.all().order_by("order", "min_points")
    serializer_class = CreatorLevelSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class BadgeAdminViewSet(ModelViewSet):
    queryset = Badge.objects.all().order_by("rarity", "code")
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT

    @action(detail=True, methods=["post"], url_path="grant")
    def grant(self, request, pk=None):
        badge = self.get_object()
        try:
            user_id = int(request.data.get("user_id", 0))
        except (TypeError, ValueError):
            return api_fail("user_id 必填", code=status.HTTP_400_BAD_REQUEST)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return api_fail("用户不存在", code=status.HTTP_404_NOT_FOUND)
        try:
            ach = services.grant_badge_manually(user=user, badge=badge)
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        from apps.operations.creator.serializers import CreatorAchievementSerializer
        return api_ok(CreatorAchievementSerializer(ach).data, message="已授予")


class CreatorProfileAdminViewSet(ModelViewSet):
    queryset = CreatorProfile.objects.select_related("user", "level").order_by("-total_points")
    serializer_class = CreatorProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT
    search_fields = ["user__username", "bio"]
    filterset_fields = ["level", "is_certified"]

    @action(detail=True, methods=["post"], url_path="adjust-points")
    def adjust_points(self, request, pk=None):
        profile = self.get_object()
        try:
            delta = int(request.data.get("delta", 0))
        except (TypeError, ValueError):
            return api_fail("delta 必填（整数）", code=status.HTTP_400_BAD_REQUEST)
        if not delta:
            return api_fail("delta 不能为 0", code=status.HTTP_400_BAD_REQUEST)
        try:
            tx = services.admin_adjust(
                user=profile.user, delta=delta,
                operator=getattr(request.user, "username", "ops"),
                note=str(request.data.get("note", ""))[:255] or "运营调整",
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(PointsTransactionSerializer(tx).data, message="已调整")

    @action(detail=True, methods=["post"], url_path="certify")
    def certify(self, request, pk=None):
        profile = self.get_object()
        from django.utils import timezone
        profile.is_certified = True
        profile.certified_at = timezone.now()
        profile.save(update_fields=["is_certified", "certified_at", "updated_at"])
        return api_ok(CreatorProfileSerializer(profile).data, message="已认证")
