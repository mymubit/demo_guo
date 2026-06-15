# -*- coding: utf-8 -*-
"""用户中心 — 会员权益矩阵。"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.membership.feature_matrix_service import FeatureMatrixService
from apps.membership.models import MembershipFeatureMatrixItem


class MembershipFeatureMatrixListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return api_ok(FeatureMatrixService.list_admin_items())

    def post(self, request):
        data = request.data or {}
        key = (data.get("feature_key") or "").strip()
        if not key:
            return api_fail("feature_key 不能为空")
        row = FeatureMatrixService.upsert(key, data)
        return api_ok(
            {"id": str(row.id), "feature_key": row.feature_key, "label": row.label},
            message="权益项已保存",
            http_status=status.HTTP_201_CREATED,
        )


class MembershipFeatureMatrixDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, item_id=None):
        try:
            row = MembershipFeatureMatrixItem.objects.get(pk=item_id)
        except MembershipFeatureMatrixItem.DoesNotExist:
            return api_fail("权益项不存在")
        data = request.data or {}
        if "label" in data:
            row.label = str(data["label"])[:128]
        if "free" in data:
            row.free = bool(data["free"])
        if "member" in data:
            row.member = bool(data["member"])
        if "coming_soon" in data:
            row.coming_soon = bool(data["coming_soon"])
        if "member_only" in data:
            row.member_only = bool(data["member_only"])
        if "is_active" in data:
            row.is_active = bool(data["is_active"])
        if "sort_order" in data:
            row.sort_order = int(data["sort_order"])
        row.save()
        return api_ok(None, message="权益项已更新")

    def delete(self, request, item_id=None):
        try:
            row = MembershipFeatureMatrixItem.objects.get(pk=item_id)
        except MembershipFeatureMatrixItem.DoesNotExist:
            return api_fail("权益项不存在")
        row.delete()
        return api_ok(None, message="权益项已删除")


class MembershipFeatureMatrixSeedView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        created = FeatureMatrixService.seed_defaults()
        return api_ok({"created": created}, message=f"已写入 {created} 条默认权益项")
