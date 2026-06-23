# -*- coding: utf-8 -*-
"""
后台管理 API 路由 — 按十大中心组织。

挂载于 /api/admin/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.console.agent.review_views import ReviewScoringConfigView
from apps.console.config.catalog_views import (
    CreationFormCatalogView,
    CreationFormImportView,
    HookDetailView,
    HookView,
    SkillConfigView,
    ThemeTemplateDetailView,
    ThemeTemplateView,
)
from apps.console.commerce.billing_views import (
    ActionPricingDetailView,
    ActionPricingListView,
    AiFieldPromptDetailView,
    AiFieldPromptListView,
    AiFieldPromptSeedView,
    RechargePackageDetailView,
    RechargePackageListView,
    SiteCoinSettingsView,
)
from apps.console.commerce.order_views import OrderManagementViewSet
from apps.console.agent.execution_views import (
    AgentCatalogAdminView,
    AgentExecutionRunDetailView,
    AgentProjectTraceView,
)
from apps.console.agent.registry_views import (
    AgentRegistryConfigView,
    IndependentAgentDetailView,
    IndependentAgentListView,
    IndependentAgentRunsListView,
    IndependentKnowledgeBindingDeleteView,
    IndependentKnowledgeBindingView,
    IndependentKnowledgeDetailView,
    IndependentKnowledgeListView,
    IndependentPromptActivateView,
    IndependentPromptListView,
)
from apps.console.skills.rule_views import (
    SkillRuleApproveView,
    SkillRuleArchiveView,
    SkillRuleDetailView,
    SkillRuleImportView,
    SkillRuleListView,
)
from apps.console.skills.rule_item_views import (
    SkillRuleItemApproveView,
    SkillRuleItemArchiveView,
    SkillRuleItemDetailView,
    SkillRuleItemFlattenView,
    SkillRuleItemListView,
)
from apps.console.skills.definition_views import (
    SkillDefinitionDetailView,
    SkillDefinitionListView,
    SkillDefinitionPublishView,
    SkillDefinitionDeprecateView,
    SkillDefinitionRollbackView,
    SkillDefinitionStatsView,
    SkillDefinitionVersionsView,
    SkillDefinitionGrayPreviewView,
    SkillConfigEntryDetailView,
    SkillConfigEntryListView,
    SkillDefectDetailView,
    SkillDefectListView,
)
from apps.console.creation.quality_defect_views import (
    ScriptQualityDefectDetailView,
    ScriptQualityDefectListView,
)
from apps.console.creation.project_views import (
    AdminCreationProjectDetailView,
    AdminCreationProjectListView,
)
from apps.console.agent.route_views import (
    AgentLlmRouteDetailView,
    AgentLlmRouteListView,
    AgentLlmRouteSeedView,
)
from apps.console.model.llm_views import (
    LlmCatalogDetailView,
    LlmCatalogListCreateView,
    LlmConfigAdminView,
    LlmConfigTestView,
    LlmEnvSetupView,
    LlmGlobalSettingsView,
    LlmPresetsSyncView,
    LlmProviderActivateView,
    LlmProviderDetailView,
    LlmProviderListCreateView,
    LlmRoutingPlanView,
    LlmUsageRecalculateView,
    LlmVendorCredentialView,
)
from apps.console.identity.user_views import UserManagementViewSet
from apps.console.identity.membership_views import (
    MembershipPlanViewSet,
    PromoCodeGenerateView,
    PromoCodeListView,
)
from apps.console.identity.feature_matrix_views import (
    MembershipFeatureMatrixDetailView,
    MembershipFeatureMatrixListView,
    MembershipFeatureMatrixSeedView,
)
from apps.console.monitor.dashboard_views import DashboardView
from apps.console.monitor.stats_views import (
    CacheClearView,
    StatsSummaryView,
    SystemSettingsView,
)
from apps.console.stats.extended_views import (
    FailureRankingView,
    LlmProviderUsageView,
    NodeDurationDistributionView,
    SkillRankingView,
    StatsKpiView,
    StatsTrendView,
)
from apps.console.system_config.extended_views import (
    GlobalSwitchView,
    QuotaRulesView,
    SensitiveWordsView,
    ThresholdConfigView,
)
from apps.creation.library.views import (
    MaterialListView,
    MaterialUploadView,
    MaterialDetailView,
    MaterialParseView,
)
from apps.skill.evolution.views import (
    EvolutionProposalListView,
    EvolutionAnalyzeView,
    EvolutionProposalDetailView,
    EvolutionApproveView,
    EvolutionRejectView,
    EvolutionApplyView,
)
from apps.system_config.urls import admin_urlpatterns as system_config_admin_urlpatterns

router = DefaultRouter()
router.register(r"users", UserManagementViewSet, basename="admin-user")
router.register(r"members/plans", MembershipPlanViewSet, basename="admin-membership-plan")
router.register(r"orders", OrderManagementViewSet, basename="admin-order")

app_name = "console"

# Agent 中心
_agent_routes = [
    path("agent/registry/", AgentRegistryConfigView.as_view(), name="admin-agent-registry"),
    path("agent/definitions/", IndependentAgentListView.as_view(), name="admin-independent-agents"),
    path("agent/definitions/<str:agent_id>/", IndependentAgentDetailView.as_view(), name="admin-independent-agent-detail"),
    path("agent/definitions/<str:agent_id>/prompts/", IndependentPromptListView.as_view(), name="admin-independent-agent-prompts"),
    path(
        "agent/definitions/<str:agent_id>/prompts/<str:version>/activate/",
        IndependentPromptActivateView.as_view(),
        name="admin-independent-agent-prompt-activate",
    ),
    path("agent/knowledge/", IndependentKnowledgeListView.as_view(), name="admin-independent-knowledge"),
    path(
        "agent/knowledge/<str:knowledge_id>/",
        IndependentKnowledgeDetailView.as_view(),
        name="admin-independent-knowledge-detail",
    ),
    path("agent/runs/", IndependentAgentRunsListView.as_view(), name="admin-independent-agent-runs"),
    path("agent/runs/<str:run_id>/", AgentExecutionRunDetailView.as_view(), name="admin-agent-run-detail"),
    path(
        "agent/projects/<str:project_id>/traces/",
        AgentProjectTraceView.as_view(),
        name="admin-agent-project-traces",
    ),
    path(
        "agent/definitions/<str:agent_id>/knowledge-bindings/",
        IndependentKnowledgeBindingView.as_view(),
        name="admin-independent-agent-knowledge-bindings",
    ),
    path(
        "agent/definitions/<str:agent_id>/knowledge-bindings/<str:binding_id>/",
        IndependentKnowledgeBindingDeleteView.as_view(),
        name="admin-independent-agent-knowledge-binding-delete",
    ),
    path("agent/llm-routes/", AgentLlmRouteListView.as_view(), name="admin-agent-llm-routes"),
    path("agent/llm-routes/seed/", AgentLlmRouteSeedView.as_view(), name="admin-agent-llm-routes-seed"),
    path("agent/llm-routes/<uuid:route_id>/", AgentLlmRouteDetailView.as_view(), name="admin-agent-llm-routes-detail"),
    path("agent/review-scoring/", ReviewScoringConfigView.as_view(), name="admin-agent-review-scoring"),
    path("agent/catalog/", AgentCatalogAdminView.as_view(), name="admin-agent-catalog"),
]

# 模型中心
_model_routes = [
    path("model/llm/", LlmConfigAdminView.as_view(), name="admin-model-llm"),
    path("model/llm/settings/", LlmGlobalSettingsView.as_view(), name="admin-model-llm-settings"),
    path("model/llm/providers/", LlmProviderListCreateView.as_view(), name="admin-model-llm-providers"),
    path("model/llm/providers/<uuid:provider_id>/", LlmProviderDetailView.as_view(), name="admin-model-llm-provider-detail"),
    path("model/llm/providers/<uuid:provider_id>/activate/", LlmProviderActivateView.as_view(), name="admin-model-llm-provider-activate"),
    path("model/llm/test/", LlmConfigTestView.as_view(), name="admin-model-llm-test"),
    path("model/llm/presets/sync/", LlmPresetsSyncView.as_view(), name="admin-model-llm-presets-sync"),
    path("model/llm/routing-plan/", LlmRoutingPlanView.as_view(), name="admin-model-llm-routing-plan"),
    path("model/llm/env-setup/", LlmEnvSetupView.as_view(), name="admin-model-llm-env-setup"),
    path("model/llm/vendors/<str:vendor>/credential/", LlmVendorCredentialView.as_view(), name="admin-model-llm-vendor-credential"),
    path("model/llm/catalog/", LlmCatalogListCreateView.as_view(), name="admin-model-llm-catalog"),
    path("model/llm/catalog/<uuid:catalog_id>/", LlmCatalogDetailView.as_view(), name="admin-model-llm-catalog-detail"),
    path("model/llm/usage/recalculate/", LlmUsageRecalculateView.as_view(), name="admin-model-llm-usage-recalculate"),
]

# 配置中心（C 端门户运营）
_portal_routes = [
    path("portal/configs/", SkillConfigView.as_view(), name="admin-portal-configs-list"),
    path("portal/configs/<str:key>/", SkillConfigView.as_view(), name="admin-portal-configs-detail"),
    path("portal/creation-form/", CreationFormCatalogView.as_view(), name="admin-portal-creation-form"),
    path("portal/creation-form/import/", CreationFormImportView.as_view(), name="admin-portal-creation-form-import"),
    path("portal/themes/", ThemeTemplateView.as_view(), name="admin-portal-themes"),
    path("portal/themes/<str:theme_id>/", ThemeTemplateDetailView.as_view(), name="admin-portal-themes-detail"),
    path("portal/hooks/", HookView.as_view(), name="admin-portal-hooks"),
    path("portal/hooks/<str:hook_id>/", HookDetailView.as_view(), name="admin-portal-hooks-detail"),
]

# 技能中心 — 写作规则
_skills_routes = [
    path("skills/rules/", SkillRuleListView.as_view(), name="admin-skills-rules-list"),
    path("skills/rules/import/", SkillRuleImportView.as_view(), name="admin-skills-rules-import"),
    path("skills/rules/<uuid:rule_id>/", SkillRuleDetailView.as_view(), name="admin-skills-rules-detail"),
    path("skills/rules/<uuid:rule_id>/approve/", SkillRuleApproveView.as_view(), name="admin-skills-rules-approve"),
    path("skills/rules/<uuid:rule_id>/archive/", SkillRuleArchiveView.as_view(), name="admin-skills-rules-archive"),
    path("skills/rule-items/", SkillRuleItemListView.as_view(), name="admin-skills-rule-items-list"),
    path("skills/rule-items/flatten/", SkillRuleItemFlattenView.as_view(), name="admin-skills-rule-items-flatten"),
    path("skills/rule-items/<uuid:item_id>/", SkillRuleItemDetailView.as_view(), name="admin-skills-rule-items-detail"),
    path("skills/rule-items/<uuid:item_id>/approve/", SkillRuleItemApproveView.as_view(), name="admin-skills-rule-items-approve"),
    path("skills/rule-items/<uuid:item_id>/archive/", SkillRuleItemArchiveView.as_view(), name="admin-skills-rule-items-archive"),
    # 技能定义（SKILL.md → DB）+ 生命周期操作
    path("skills/definitions/", SkillDefinitionListView.as_view(), name="admin-skills-definitions-list"),
    path("skills/definitions/<int:pk>/", SkillDefinitionDetailView.as_view(), name="admin-skills-definitions-detail"),
    path("skills/definitions/<int:pk>/publish/", SkillDefinitionPublishView.as_view(), name="admin-skills-definitions-publish"),
    path("skills/definitions/<int:pk>/deprecate/", SkillDefinitionDeprecateView.as_view(), name="admin-skills-definitions-deprecate"),
    path("skills/definitions/<int:pk>/rollback/", SkillDefinitionRollbackView.as_view(), name="admin-skills-definitions-rollback"),
    path("skills/definitions/<int:pk>/versions/", SkillDefinitionVersionsView.as_view(), name="admin-skills-definitions-versions"),
    path("skills/definitions/stats/", SkillDefinitionStatsView.as_view(), name="admin-skills-definitions-stats"),
    path("skills/definitions/gray-preview/", SkillDefinitionGrayPreviewView.as_view(), name="admin-skills-definitions-gray-preview"),
    # 技能配置项
    path("skills/configs/", SkillConfigEntryListView.as_view(), name="admin-skills-configs-list"),
    path("skills/configs/<str:config_key>/", SkillConfigEntryDetailView.as_view(), name="admin-skills-configs-detail"),
    # 技能缺陷
    path("skills/defects/", SkillDefectListView.as_view(), name="admin-skills-defects-list"),
    path("skills/defects/<int:pk>/", SkillDefectDetailView.as_view(), name="admin-skills-defects-detail"),
    # 剧本质量缺陷
    path("creation/quality-defects/", ScriptQualityDefectListView.as_view(), name="admin-creation-quality-defects"),
    path("creation/quality-defects/<int:pk>/", ScriptQualityDefectDetailView.as_view(), name="admin-creation-quality-defect-detail"),
]

# 数据统计中心扩展
_stats_routes = [
    path("stats/kpi/", StatsKpiView.as_view(), name="admin-stats-kpi"),
    path("stats/trend/", StatsTrendView.as_view(), name="admin-stats-trend"),
    path("stats/skill-ranking/", SkillRankingView.as_view(), name="admin-stats-skill-ranking"),
    path("stats/failure-ranking/", FailureRankingView.as_view(), name="admin-stats-failure-ranking"),
    path("stats/llm-provider-usage/", LlmProviderUsageView.as_view(), name="admin-stats-llm-provider-usage"),
    path("stats/node-duration/", NodeDurationDistributionView.as_view(), name="admin-stats-node-duration"),
]

# 系统配置中心扩展
_system_routes = [
    path("system/global-switch/", GlobalSwitchView.as_view(), name="admin-system-global-switch"),
    path("system/thresholds/", ThresholdConfigView.as_view(), name="admin-system-thresholds"),
    path("system/quota-rules/", QuotaRulesView.as_view(), name="admin-system-quota-rules"),
    path("system/sensitive-words/", SensitiveWordsView.as_view(), name="admin-system-sensitive-words"),
]

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", DashboardView.as_view(), name="admin-dashboard"),
    path("monitoring/", include("apps.monitoring.admin_urls")),
    path("members/codes/", PromoCodeListView.as_view(), name="admin-promo-code-list"),
    path("members/codes/generate/", PromoCodeGenerateView.as_view(), name="admin-promo-code-generate"),
    path("creation/projects/", AdminCreationProjectListView.as_view(), name="admin-creation-projects"),
    path("creation/projects/<str:project_id>/", AdminCreationProjectDetailView.as_view(), name="admin-creation-project-detail"),
    path("members/feature-matrix/", MembershipFeatureMatrixListView.as_view(), name="admin-members-feature-matrix"),
    path("members/feature-matrix/seed/", MembershipFeatureMatrixSeedView.as_view(), name="admin-members-feature-matrix-seed"),
    path("members/feature-matrix/<uuid:item_id>/", MembershipFeatureMatrixDetailView.as_view(), name="admin-members-feature-matrix-detail"),
    path("stats/summary/", StatsSummaryView.as_view(), name="admin-stats-summary"),
    path("system/settings/", SystemSettingsView.as_view(), name="admin-system-settings"),
    path("system/cache/clear/", CacheClearView.as_view(), name="admin-system-cache-clear"),
    path("system/", include((system_config_admin_urlpatterns, "system-config"))),
    path("billing/settings/", SiteCoinSettingsView.as_view(), name="admin-billing-settings"),
    path("billing/pricing/", ActionPricingListView.as_view(), name="admin-billing-pricing"),
    path("billing/pricing/<uuid:pricing_id>/", ActionPricingDetailView.as_view(), name="admin-billing-pricing-detail"),
    path("billing/recharge/", RechargePackageListView.as_view(), name="admin-billing-recharge"),
    path("billing/recharge/<uuid:package_id>/", RechargePackageDetailView.as_view(), name="admin-billing-recharge-detail"),
    path("billing/ai-prompts/", AiFieldPromptListView.as_view(), name="admin-billing-ai-prompts"),
    path("billing/ai-prompts/seed/", AiFieldPromptSeedView.as_view(), name="admin-billing-ai-prompts-seed"),
    path("billing/ai-prompts/<uuid:prompt_id>/", AiFieldPromptDetailView.as_view(), name="admin-billing-ai-prompts-detail"),
    # 十大中心前缀
    *_agent_routes,
    *_model_routes,
    *_portal_routes,
    *_skills_routes,
    *_stats_routes,
    *_system_routes,
]

# 素材库
_library_routes = [
    path("creation/library/materials/", MaterialListView.as_view(), name="admin-library-materials-list"),
    path("creation/library/materials/upload/", MaterialUploadView.as_view(), name="admin-library-materials-upload"),
    path("creation/library/materials/<uuid:material_id>/", MaterialDetailView.as_view(), name="admin-library-material-detail"),
    path("creation/library/materials/<uuid:material_id>/parse/", MaterialParseView.as_view(), name="admin-library-material-parse"),
]

# AI 规则进化
_evolution_routes = [
    path("skills/evolution/", EvolutionProposalListView.as_view(), name="admin-skills-evolution-list"),
    path("skills/evolution/analyze/", EvolutionAnalyzeView.as_view(), name="admin-skills-evolution-analyze"),
    path("skills/evolution/<uuid:proposal_id>/", EvolutionProposalDetailView.as_view(), name="admin-skills-evolution-detail"),
    path("skills/evolution/<uuid:proposal_id>/approve/", EvolutionApproveView.as_view(), name="admin-skills-evolution-approve"),
    path("skills/evolution/<uuid:proposal_id>/reject/", EvolutionRejectView.as_view(), name="admin-skills-evolution-reject"),
    path("skills/evolution/<uuid:proposal_id>/apply/", EvolutionApplyView.as_view(), name="admin-skills-evolution-apply"),
]

urlpatterns += [
    *_library_routes,
    *_evolution_routes,
]

# ── 运营监控中心（apps.operations）──────────────────────────
from apps.operations.urls import admin_urlpatterns as operations_admin_urlpatterns

urlpatterns += [
    path("operations/", include((operations_admin_urlpatterns, "operations"))),
]
