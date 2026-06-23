# -*- coding: utf-8 -*-
"""
会员模块路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    FeatureMatrixView,
    MembershipPlanViewSet,
    MyMembershipView,
    MembershipSummaryView,
    MyMembershipHistoryView,
    RedeemPromoCodeView,
)

router = DefaultRouter()
router.register(r"plans", MembershipPlanViewSet, basename="membership-plan")

urlpatterns = [
    path("", include(router.urls)),
    path("me/", MyMembershipView.as_view(), name="my-membership"),
    path("summary/", MembershipSummaryView.as_view(), name="membership-summary"),
    path("feature-matrix/", FeatureMatrixView.as_view(), name="membership-feature-matrix"),
    path("history/", MyMembershipHistoryView.as_view(), name="my-membership-history"),
    path("redeem/", RedeemPromoCodeView.as_view(), name="redeem-promo-code"),
]
