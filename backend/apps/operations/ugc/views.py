"""UGC 模板市场 API。"""
from __future__ import annotations

import logging

from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.operations.exceptions import OperationsError
from apps.operations.permissions import DOMAIN_CONTENT, HasOpsDomain
from apps.operations.ugc import services
from apps.operations.ugc.models import (
    UserTemplate,
    UserTemplateCollection,
    UserTemplateRating,
)
from apps.operations.ugc.serializers import (
    UserTemplateCollectionSerializer,
    UserTemplateCreateSerializer,
    UserTemplateDetailSerializer,
    UserTemplateListSerializer,
    UserTemplateRatingSerializer,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 前台：浏览 / 搜索 / 我的
# ──────────────────────────────────────────────

class UgcTemplateBrowseView(GenericAPIView):
    """前台浏览/搜索 UGC 模板（无需运营角色）。"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserTemplateListSerializer

    def get(self, request):
        keyword = request.query_params.get("keyword", "").strip()
        category = request.query_params.get("category", "").strip()
        tag = request.query_params.get("tag", "").strip()
        ordering = request.query_params.get("ordering", "popular")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        try:
            result = services.search_templates(
                keyword=keyword, category=category, tag=tag,
                ordering=ordering, page=page, page_size=page_size,
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        data = UserTemplateListSerializer(result["items"], many=True).data
        return api_ok({
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "items": data,
        })


class UgcTemplateDetailView(GenericAPIView):
    """前台模板详情。"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserTemplateDetailSerializer

    def get(self, request, slug: str):
        try:
            tpl = UserTemplate.objects.get(slug=slug, status="published")
        except UserTemplate.DoesNotExist:
            return api_fail("模板不存在", code=status.HTTP_404_NOT_FOUND)
        return api_ok(UserTemplateDetailSerializer(tpl).data)


class UgcTemplatePublishView(GenericAPIView):
    """前台：创作者发布模板。"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserTemplateCreateSerializer

    def post(self, request):
        serializer = UserTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tpl = services.publish_template(
                author=request.user,
                auto_submit=request.data.get("auto_submit", True),
                **serializer.validated_data,
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(UserTemplateDetailSerializer(tpl).data, message="已提交")


class UgcTemplateRateView(GenericAPIView):
    """前台：评分。"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserTemplateRatingSerializer

    def post(self, request, slug: str):
        try:
            tpl = UserTemplate.objects.get(slug=slug, status="published")
        except UserTemplate.DoesNotExist:
            return api_fail("模板不存在", code=status.HTTP_404_NOT_FOUND)
        score = int(request.data.get("score", 0))
        comment = str(request.data.get("comment", ""))
        try:
            rating = services.rate_template(
                template=tpl, user=request.user, score=score, comment=comment,
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(UserTemplateRatingSerializer(rating).data, message="评分成功")


class UgcTemplateCollectView(GenericAPIView):
    """前台：收藏 / 取消收藏。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, slug: str):
        try:
            tpl = UserTemplate.objects.get(slug=slug, status="published")
        except UserTemplate.DoesNotExist:
            return api_fail("模板不存在", code=status.HTTP_404_NOT_FOUND)
        try:
            obj = services.collect_template(
                template=tpl, user=request.user,
                collection_name=str(request.data.get("collection_name", ""))[:64],
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(UserTemplateCollectionSerializer(obj).data, message="已收藏")

    def delete(self, request, slug: str):
        try:
            tpl = UserTemplate.objects.get(slug=slug)
        except UserTemplate.DoesNotExist:
            return api_fail("模板不存在", code=status.HTTP_404_NOT_FOUND)
        ok = services.uncollect_template(template=tpl, user=request.user)
        return api_ok({"uncollected": ok})


class UgcTemplateDownloadView(GenericAPIView):
    """前台：下载（返回快照 + 计数 +1）。"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserTemplateDetailSerializer

    def get(self, request, slug: str):
        try:
            tpl = UserTemplate.objects.get(slug=slug, status="published")
        except UserTemplate.DoesNotExist:
            return api_fail("模板不存在", code=status.HTTP_404_NOT_FOUND)
        try:
            tpl = services.download_template(template=tpl)
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok({
            "template": UserTemplateListSerializer(tpl).data,
            "pack_snapshot": tpl.pack_snapshot,
        })


class MyUgcCollectionsView(ListModelMixin, GenericAPIView):
    """我的收藏。"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserTemplateCollectionSerializer

    def get(self, request, *args, **kwargs):
        self.queryset = UserTemplateCollection.objects.filter(user=request.user).order_by("-created_at")
        return self.list(request, *args, **kwargs)


# ──────────────────────────────────────────────
# 运营：审核 / 置顶
# ──────────────────────────────────────────────

class UgcTemplateAdminViewSet(ModelViewSet):
    """运营：UGC 模板审核 / 置顶 / 下架。"""

    queryset = UserTemplate.objects.all().order_by("-created_at")
    serializer_class = UserTemplateDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT
    search_fields = ["name", "description", "category", "slug"]
    filterset_fields = ["status", "category", "is_featured", "author"]

    @action(detail=True, methods=["post"], url_path="review")
    def review(self, request, pk=None):
        tpl = self.get_object()
        try:
            tpl = services.review_template(
                tpl,
                approve=bool(request.data.get("approve", False)),
                reviewer=request.user,
                note=str(request.data.get("note", ""))[:1000],
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(UserTemplateDetailSerializer(tpl).data, message="审核完成")

    @action(detail=True, methods=["post"], url_path="offline")
    def offline(self, request, pk=None):
        tpl = self.get_object()
        try:
            tpl = services.offline_template(
                tpl, operator=request.user,
                note=str(request.data.get("note", ""))[:500],
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(UserTemplateDetailSerializer(tpl).data, message="已下架")

    @action(detail=True, methods=["post"], url_path="feature")
    def feature(self, request, pk=None):
        tpl = self.get_object()
        try:
            tpl = services.set_featured(
                tpl,
                featured=bool(request.data.get("featured", True)),
                sort_weight=int(request.data.get("sort_weight", 0)),
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(UserTemplateDetailSerializer(tpl).data, message="已更新置顶")
