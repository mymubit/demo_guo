"""运营活动 URL。"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CampaignViewSet,
    CouponClaimLogViewSet,
    CouponTemplateViewSet,
    RedemptionCodeBatchViewSet,
    RedemptionCodeViewSet,
    UserCouponClaimView,
    UserCouponListView,
)

router = DefaultRouter()
router.register(r"campaigns", CampaignViewSet, basename="ops-campaign")
router.register(r"coupons/templates", CouponTemplateViewSet, basename="ops-coupon-template")
router.register(r"coupons/code-batches", RedemptionCodeBatchViewSet, basename="ops-code-batch")
router.register(r"coupons/codes", RedemptionCodeViewSet, basename="ops-code")
router.register(r"coupons/claim-logs", CouponClaimLogViewSet, basename="ops-claim-log")

urlpatterns = router.urls + [
    # C 端用户接口
    path("my/coupons/", UserCouponListView.as_view(), name="ops-my-coupons"),
    path("my/coupons/claim/", UserCouponClaimView.as_view(), name="ops-my-coupons-claim"),
]
