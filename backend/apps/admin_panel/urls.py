"""
后台管理 API 路由

所有路由前缀（见 config/urls.py）：/api/admin/

- 技能配置 / 题材模板 / 钩子库 路由与 skill 模块独立维护
（skill 模块使用 /api/skill/configs/ 等，本文件为 /api/admin/skill/configs/ 等）
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


# 视图集路由（/api/admin/users/, /api/admin/members/plans/, /api/admin/orders/）
router = DefaultRouter()
router.register(r"users", UserManagementViewSet, basename="admin-user")
router.register(r"members/plans", MembershipPlanViewSet, basename="admin-membership-plan")
router.register(r"orders", OrderManagementViewSet, basename="admin-order")


app_name = "admin_panel"

urlpatterns = [
    # 基础视图集路由
    path("", include(router.urls)),

    # Dashboard
    path("dashboard/", DashboardView.as_view(), name="admin-dashboard"),

    # 会员 - 批量生成卡密
    path(
        "members/codes/generate/",
        PromoCodeGenerateView.as_view(),
        name="admin-promo-code-generate",
    ),

    # 技能配置（对接 apps.skill.models.SkillConfig 表）
    # 列表 / 单条更新，共用 SkillConfigView；由 URL 参数区分
    path("skill/configs/", SkillConfigView.as_view(), name="admin-skill-configs-list"),
    path(
        "skill/configs/<str:key>/",
        SkillConfigView.as_view(),
        name="admin-skill-configs-detail",
    ),

    # 题材模板（对接 apps.skill.models.ThemeTemplate 表）
    path("skill/themes/", ThemeTemplateView.as_view(), name="admin-skill-themes"),
    path(
        "skill/themes/<str:theme_id>/",
        ThemeTemplateDetailView.as_view(),
        name="admin-skill-themes-detail",
    ),

    # 钩子库（对接 apps.skill.models.HookLibrary 表）
    path("skill/hooks/", HookView.as_view(), name="admin-skill-hooks"),

    # 统计总览
    path("stats/summary/", StatsSummaryView.as_view(), name="admin-stats-summary"),

    # 系统设置 / 缓存
    path("system/settings/", SystemSettingsView.as_view(), name="admin-system-settings"),
    path("system/cache/clear/", CacheClearView.as_view(), name="admin-cache-clear"),
]
