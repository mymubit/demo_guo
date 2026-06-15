from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.monitoring.views import (
    AlertEventViewSet,
    AlertRuleViewSet,
    ApiPerformanceViewSet,
    FrontendEventViewSet,
    MonitoringExceptionViewSet,
    MonitoringHealthView,
    MonitoringOverviewView,
    SlowSqlViewSet,
)

router = DefaultRouter()
router.register("frontend-events", FrontendEventViewSet, basename="admin-monitoring-frontend-event")
router.register("exceptions", MonitoringExceptionViewSet, basename="admin-monitoring-exception")
router.register("api-performance", ApiPerformanceViewSet, basename="admin-monitoring-api-performance")
router.register("slow-sql", SlowSqlViewSet, basename="admin-monitoring-slow-sql")
router.register("alert-rules", AlertRuleViewSet, basename="admin-monitoring-alert-rule")
router.register("alert-events", AlertEventViewSet, basename="admin-monitoring-alert-event")

app_name = "monitoring_admin"

urlpatterns = [
    path("overview/", MonitoringOverviewView.as_view(), name="overview"),
    path("health/", MonitoringHealthView.as_view(), name="health"),
    path("", include(router.urls)),
]
