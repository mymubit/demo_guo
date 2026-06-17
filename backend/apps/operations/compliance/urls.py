"""合规规则 URL。"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ComplianceCheckView,
    ComplianceRuleAdminViewSet,
    ComplianceVersionAdminViewSet,
    SensitiveWordAdminViewSet,
    TopicBlacklistAdminViewSet,
    ViolationLogAdminViewSet,
)

router = DefaultRouter()
router.register(r"compliance/sensitive-words", SensitiveWordAdminViewSet, basename="ops-compliance-sw")
router.register(r"compliance/topic-blacklist", TopicBlacklistAdminViewSet, basename="ops-compliance-tb")
router.register(r"compliance/rules", ComplianceRuleAdminViewSet, basename="ops-compliance-rule")
router.register(r"compliance/violation-logs", ViolationLogAdminViewSet, basename="ops-compliance-violation")
router.register(r"compliance/versions", ComplianceVersionAdminViewSet, basename="ops-compliance-version")

urlpatterns = [
    path("compliance/check/", ComplianceCheckView.as_view(), name="ops-compliance-check"),
] + router.urls
