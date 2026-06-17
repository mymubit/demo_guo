"""A/B 实验 URL。"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AssignmentViewSet,
    ClientAssignView,
    ClientEventView,
    ConversionLogViewSet,
    ExperimentMetricSnapshotViewSet,
    ExperimentViewSet,
    ExposureLogViewSet,
    VariantViewSet,
)

router = DefaultRouter()
router.register(r"experiments", ExperimentViewSet, basename="ops-experiment")
router.register(r"experiment-variants", VariantViewSet, basename="ops-experiment-variant")
router.register(r"experiment-assignments", AssignmentViewSet, basename="ops-experiment-assignment")
router.register(r"experiment-exposures", ExposureLogViewSet, basename="ops-experiment-exposure")
router.register(r"experiment-conversions", ConversionLogViewSet, basename="ops-experiment-conversion")
router.register(
    r"experiment-snapshots", ExperimentMetricSnapshotViewSet, basename="ops-experiment-snapshot",
)

urlpatterns = router.urls + [
    # C 端 SDK 接口
    path("sdk/assign/", ClientAssignView.as_view(), name="ops-sdk-assign"),
    path("sdk/event/", ClientEventView.as_view(), name="ops-sdk-event"),
]
