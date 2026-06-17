"""创作者激励 URL。"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BadgeAdminViewSet,
    CreatorLevelAdminViewSet,
    CreatorProfileAdminViewSet,
    LevelListView,
    MyAchievementsView,
    MyCreatorProfileView,
    MyPointsAccountView,
    MyPointsTransactionsView,
)

router = DefaultRouter()
router.register(r"creator/levels", CreatorLevelAdminViewSet, basename="ops-creator-level")
router.register(r"creator/badges", BadgeAdminViewSet, basename="ops-creator-badge")
router.register(r"creator/profiles", CreatorProfileAdminViewSet, basename="ops-creator-profile")

urlpatterns = [
    # 前台
    path("creator/my-profile/", MyCreatorProfileView.as_view(), name="ops-creator-my-profile"),
    path("creator/my-points/", MyPointsAccountView.as_view(), name="ops-creator-my-points"),
    path("creator/my-transactions/", MyPointsTransactionsView.as_view(), name="ops-creator-my-tx"),
    path("creator/my-achievements/", MyAchievementsView.as_view(), name="ops-creator-my-ach"),
    path("creator/level-list/", LevelListView.as_view(), name="ops-creator-level-list"),
] + router.urls
