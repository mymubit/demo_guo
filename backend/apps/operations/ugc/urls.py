"""UGC 模板市场 URL。"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    MyUgcCollectionsView,
    UgcTemplateAdminViewSet,
    UgcTemplateBrowseView,
    UgcTemplateCollectView,
    UgcTemplateDetailView,
    UgcTemplateDownloadView,
    UgcTemplatePublishView,
    UgcTemplateRateView,
)

router = DefaultRouter()
router.register(r"ugc/admin", UgcTemplateAdminViewSet, basename="ops-ugc-admin")

urlpatterns = [
    # 前台
    path("ugc/browse/", UgcTemplateBrowseView.as_view(), name="ops-ugc-browse"),
    path("ugc/publish/", UgcTemplatePublishView.as_view(), name="ops-ugc-publish"),
    path("ugc/my-collections/", MyUgcCollectionsView.as_view(), name="ops-ugc-my-collections"),
    path("ugc/<slug:slug>/", UgcTemplateDetailView.as_view(), name="ops-ugc-detail"),
    path("ugc/<slug:slug>/rate/", UgcTemplateRateView.as_view(), name="ops-ugc-rate"),
    path("ugc/<slug:slug>/collect/", UgcTemplateCollectView.as_view(), name="ops-ugc-collect"),
    path("ugc/<slug:slug>/download/", UgcTemplateDownloadView.as_view(), name="ops-ugc-download"),
] + router.urls
