"""
技能配置模块路由

前缀 /api/skill/
"""
from django.urls import path

from .views import (
    SkillConfigListView,
    SkillConfigUpdateView,
    ThemeTemplateListView,
    ThemeTemplateUpdateView,
    HookLibraryListView,
    ThemePublicListView,
)

app_name = "skill"

urlpatterns = [
    # 技能配置（管理员）
    path("configs/", SkillConfigListView.as_view(), name="config-list"),
    path("configs/<str:config_key>/", SkillConfigUpdateView.as_view(), name="config-update"),

    # 题材模板（管理员）
    path("themes/", ThemeTemplateListView.as_view(), name="theme-list"),
    path("themes/<int:theme_id>/", ThemeTemplateUpdateView.as_view(), name="theme-update"),

    # 钩子库（管理员）
    path("hooks/", HookLibraryListView.as_view(), name="hook-list"),

    # 公共题材列表（登录用户可读取）
    path("themes/public/", ThemePublicListView.as_view(), name="themes-public"),
]
