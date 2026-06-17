"""合规规则 API。"""
from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.operations.compliance import services
from apps.operations.compliance.models import (
    ComplianceRule,
    ComplianceRuleVersion,
    SensitiveWord,
    TopicBlacklist,
    ViolationLog,
)
from apps.operations.compliance.serializers import (
    ComplianceRuleSerializer,
    ComplianceRuleVersionSerializer,
    SensitiveWordSerializer,
    TopicBlacklistSerializer,
    ViolationLogSerializer,
)
from apps.operations.exceptions import OperationsError
from apps.operations.permissions import DOMAIN_CONTENT, HasOpsDomain

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 运营：敏感词 / 黑名单 / 规则
# ──────────────────────────────────────────────

class SensitiveWordAdminViewSet(ModelViewSet):
    queryset = SensitiveWord.objects.all().order_by("-updated_at")
    serializer_class = SensitiveWordSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT
    search_fields = ["word", "description"]
    filterset_fields = ["category", "level", "is_active"]

    def perform_create(self, serializer):
        try:
            services.upsert_sensitive_word(
                word=serializer.validated_data["word"],
                category=serializer.validated_data["category"],
                level=serializer.validated_data["level"],
                description=serializer.validated_data.get("description", ""),
                is_active=serializer.validated_data.get("is_active", True),
                operator=getattr(self.request.user, "username", ""),
            )
        except OperationsError as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(e.message)


class TopicBlacklistAdminViewSet(ModelViewSet):
    queryset = TopicBlacklist.objects.all().order_by("-updated_at")
    serializer_class = TopicBlacklistSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT
    search_fields = ["name", "reason"]
    filterset_fields = ["category", "level", "is_active"]


class ComplianceRuleAdminViewSet(ModelViewSet):
    queryset = ComplianceRule.objects.all().order_by("-updated_at")
    serializer_class = ComplianceRuleSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT
    search_fields = ["name", "description"]
    filterset_fields = ["category", "level", "scope", "is_active"]


class ViolationLogAdminViewSet(ModelViewSet):
    queryset = ViolationLog.objects.all().order_by("-created_at")
    serializer_class = ViolationLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT
    http_method_names = ["get", "post", "head", "options"]  # 不可改 / 不可删
    filterset_fields = ["category", "level", "handled", "source"]
    search_fields = ["matched_text", "rule_name", "user__username"]

    @action(detail=True, methods=["post"], url_path="handle")
    def handle(self, request, pk=None):
        v = self.get_object()
        try:
            v = services.handle_violation(
                v.pk,
                operator=getattr(request.user, "username", "ops"),
                note=str(request.data.get("note", ""))[:1000],
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(ViolationLogSerializer(v).data, message="已处理")


# ──────────────────────────────────────────────
# 运营：版本 / 测试
# ──────────────────────────────────────────────

class ComplianceVersionAdminViewSet(ModelViewSet):
    queryset = ComplianceRuleVersion.objects.all().order_by("-published_at")
    serializer_class = ComplianceRuleVersionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_CONTENT
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=False, methods=["post"], url_path="publish")
    def publish(self, request):
        try:
            v = services.publish_version(
                note=str(request.data.get("note", ""))[:1000],
                operator=getattr(request.user, "username", "ops"),
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(ComplianceRuleVersionSerializer(v).data, message="已发布新版本")


class ComplianceCheckView(GenericAPIView):
    """合规检查（创作管线调用，也支持运营人工试跑）。"""

    permission_classes = [IsAuthenticated]
    serializer_class = SensitiveWordSerializer

    def post(self, request):
        text = str(request.data.get("text", ""))
        scope = str(request.data.get("scope", "all"))
        hits = services.check_text(text, scope=scope)
        # 命中是否要写违规日志：靠 caller 传 record=true
        if str(request.data.get("record", "")).lower() in ("1", "true", "yes"):
            project_id = request.data.get("project_id")
            project = None
            if project_id:
                from apps.creation.models import Project
                try:
                    project = Project.objects.get(pk=project_id)
                except Project.DoesNotExist:
                    project = None
            services.record_violations(
                user=request.user, project=project, hits=hits,
                source=str(request.data.get("source", "manual"))[:32],
            )
        return api_ok({
            "hits": hits,
            "blocked": services.has_blocking_hit(hits),
            "scope": scope,
        })
