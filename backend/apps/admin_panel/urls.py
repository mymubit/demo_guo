"""
后台管理 API 路由

所有路由前缀（见 config/urls.py）：/api/admin/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.admin_panel.views import (
    DashboardView,
    UserManagementViewSet,
    MembershipPlanViewSet,
    PromoCodeGenerateView,
    SkillConfigView,
    ThemeTemplateView,
    ThemeTemplateDetailView,
    HookView,
    OrderManagementViewSet,
    StatsSummaryView,
    SystemSettingsView,
    CacheClearView,
)


# 视图集路由
router = DefaultRouter()
router.register(r"users", UserManagementViewSet, basename="admin-user")
router.register(r"members/plans", MembershipPlanViewSet, basename="admin-membership-plan")
router.register(r"orders", OrderManagementViewSet, basename="admin-order")


app_name = "admin_panel"

urlpatterns = [
    # 基础视图集路由（/api/admin/users/, /api/admin/members/plans/, /api/admin/orders/）
    path("", include(router.urls)),
    # Dashboard
    path("dashboard/", DashboardView.as_view(), name="admin-dashboard"),
    # 会员 - 批量生成卡密
    path(
        "members/codes/generate/",
        PromoCodeGenerateView.as_view(),
        name="admin-promo-code-generate",
    ),
    # 技能配置 - 列表 / 单条更新
    path("skill/configs/", SkillConfigView.as_view(), name="admin-skill-configs-list"),
    path(
        "skill/configs/<str:key>/",
        SkillConfigView.as_view(),
        name="admin-skill-configs-update",
    ),
    # 题材模板
    path("skill/themes/", ThemeTemplateView.as_view(), name="admin-skill-themes"),
    path(
        "skill/themes/<str:theme_id>/",
        ThemeTemplateDetailView.as_view(),
        name="admin-skill-themes-update",
    ),
    # 钩子库
    path("skill/hooks/", HookView.as_view(), name="admin-skill-hooks"),
    # 统计
    path("stats/summary/", StatsSummaryView.as_view(), name="admin-stats-summary"),
    # 系统
    path("system/settings/", SystemSettingsView.as_view(), name="admin-system-settings"),
    path("system/cache/clear/", CacheClearView.as_view(), name="admin-cache-clear"),
]
