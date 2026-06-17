"""运营数据看板 URL。"""
from django.urls import path

from .views import (
    ConversionAnalyticsView,
    CoreOverviewView,
    CreationAnalyticsView,
    FeatureUsageAnalyticsView,
    UserAnalyticsView,
)

urlpatterns = [
    path("dashboard/core/", CoreOverviewView.as_view(), name="ops-dashboard-core"),
    path("dashboard/users/", UserAnalyticsView.as_view(), name="ops-dashboard-users"),
    path("dashboard/creation/", CreationAnalyticsView.as_view(), name="ops-dashboard-creation"),
    path("dashboard/conversion/", ConversionAnalyticsView.as_view(), name="ops-dashboard-conversion"),
    path("dashboard/feature-usage/", FeatureUsageAnalyticsView.as_view(), name="ops-dashboard-feature"),
]
