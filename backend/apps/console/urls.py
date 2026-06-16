"""
后台管理 API 路由 — 按十大中心组织。

挂载于 /api/admin/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.console.workflow.fusion_views import (
    FusionPipelineImportView,
    FusionPipelineMetaView,
    FusionPipelinePackActivateView,
    FusionPipelinePackDetailView,
    FusionPipelinePackListView,
    FusionPipelinePackPublishView,
    FusionPipelinePackSetDefaultView,
)
from apps.console.workflow.pipeline_views import (
    PipelineStepListView,
    PipelineStepSyncView,
)
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
from apps.console.orchestration.execution_views import (
    AgentCatalogAdminView,
    AgentExecutionRunDetailView,
    AgentProjectTraceView,
    AgentSubSkillStatsView,
    OrchestrationRecentRunsView,
)
from apps.console.orchestration.flow_views import (
    OrchestrationFlowBlueprintView,
    OrchestrationFlowPublishView,
    OrchestrationFlowRegistryMetaView,
    OrchestrationFlowStepPatchView,
    OrchestrationFlowStepsReorderView,
)
from apps.console.agent.registry_views import (
    AgentRegistryConfigView,
    AgentRegistryImportView,
    AgentRegistryMigrateView,
)
from apps.console.skills.rule_views import (
    SkillRuleApproveView,
    SkillRuleArchiveView,
    SkillRuleDetailView,
    SkillRuleImportView,
    SkillRuleListView,
)
from apps.console.skills.definition_views import (
    SkillDefinitionDetailView,
    SkillDefinitionListView,
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
from apps.console.main_chain.blueprint_views import (
    MainChainBlueprintView,
    MainChainRegistryMetaView,
    MainChainStepPatchView,
)
from apps.system_config.urls import admin_urlpatterns as system_config_admin_urlpatterns

router = DefaultRouter()
router.register(r"users", UserManagementViewSet, basename="admin-user")
router.register(r"members/plans", MembershipPlanViewSet, basename="admin-membership-plan")
router.register(r"orders", OrderManagementViewSet, basename="admin-order")

app_name = "console"

# 主链工作室
_main_chain_routes = [
    path("main-chain/blueprint/", MainChainBlueprintView.as_view(), name="admin-main-chain-blueprint"),
    path("main-chain/registry-meta/", MainChainRegistryMetaView.as_view(), name="admin-main-chain-registry-meta"),
    path("main-chain/steps/<uuid:step_id>/", MainChainStepPatchView.as_view(), name="admin-main-chain-step-patch"),
    path("main-chain/steps/", PipelineStepListView.as_view(), name="admin-main-chain-steps"),
    path("main-chain/steps/sync/", PipelineStepSyncView.as_view(), name="admin-main-chain-steps-sync"),
    path("main-chain/fusion/meta/", FusionPipelineMetaView.as_view(), name="admin-main-chain-fusion-meta"),
    path("main-chain/fusion/import/", FusionPipelineImportView.as_view(), name="admin-main-chain-fusion-import"),
    path("main-chain/fusion/packs/", FusionPipelinePackListView.as_view(), name="admin-main-chain-fusion-packs"),
    path(
        "main-chain/fusion/packs/<uuid:pack_id>/",
        FusionPipelinePackDetailView.as_view(),
        name="admin-main-chain-fusion-pack-detail",
    ),
    path(
        "main-chain/fusion/packs/<uuid:pack_id>/activate/",
        FusionPipelinePackActivateView.as_view(),
        name="admin-main-chain-fusion-pack-activate",
    ),
    path(
        "main-chain/fusion/packs/<uuid:pack_id>/set-default/",
        FusionPipelinePackSetDefaultView.as_view(),
        name="admin-main-chain-fusion-pack-set-default",
    ),
    path(
        "main-chain/fusion/packs/<uuid:pack_id>/publish/",
        FusionPipelinePackPublishView.as_view(),
        name="admin-main-chain-fusion-pack-publish",
    ),
]

# Agent 中心
_agent_routes = [
    path("agent/registry/", AgentRegistryConfigView.as_view(), name="admin-agent-registry"),
    path("agent/registry/import/", AgentRegistryImportView.as_view(), name="admin-agent-registry-import"),
    path("agent/registry/migrate/", AgentRegistryMigrateView.as_view(), name="admin-agent-registry-migrate"),
    path("agent/llm-routes/", AgentLlmRouteListView.as_view(), name="admin-agent-llm-routes"),
    path("agent/llm-routes/seed/", AgentLlmRouteSeedView.as_view(), name="admin-agent-llm-routes-seed"),
    path("agent/llm-routes/<uuid:route_id>/", AgentLlmRouteDetailView.as_view(), name="admin-agent-llm-routes-detail"),
    path("agent/review-scoring/", ReviewScoringConfigView.as_view(), name="admin-agent-review-scoring"),
    path("agent/catalog/", AgentCatalogAdminView.as_view(), name="admin-agent-catalog"),
]

# 调度监察 + 流程编排
_orchestration_routes = [
    path("orchestration/flow/blueprint/", OrchestrationFlowBlueprintView.as_view(), name="admin-orchestration-flow-blueprint"),
    path(
        "orchestration/flow/steps/reorder/",
        OrchestrationFlowStepsReorderView.as_view(),
        name="admin-orchestration-flow-steps-reorder",
    ),
    path(
        "orchestration/flow/steps/<uuid:step_id>/",
        OrchestrationFlowStepPatchView.as_view(),
        name="admin-orchestration-flow-step-patch",
    ),
    path(
        "orchestration/flow/registry-meta/",
        OrchestrationFlowRegistryMetaView.as_view(),
        name="admin-orchestration-flow-registry-meta",
    ),
    path(
        "orchestration/flow/publish/",
        OrchestrationFlowPublishView.as_view(),
        name="admin-orchestration-flow-publish",
    ),
    path("orchestration/stats/", AgentSubSkillStatsView.as_view(), name="admin-orchestration-stats"),
    path(
        "orchestration/recent-runs/",
        OrchestrationRecentRunsView.as_view(),
        name="admin-orchestration-recent-runs",
    ),
    path(
        "orchestration/projects/<str:project_id>/traces/",
        AgentProjectTraceView.as_view(),
        name="admin-orchestration-project-traces",
    ),
    path(
        "orchestration/execution-runs/<str:run_id>/",
        AgentExecutionRunDetailView.as_view(),
        name="admin-orchestration-execution-run-detail",
    ),
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
    # 技能定义（SKILL.md → DB）
    path("skills/definitions/", SkillDefinitionListView.as_view(), name="admin-skills-definitions-list"),
    path("skills/definitions/<int:pk>/", SkillDefinitionDetailView.as_view(), name="admin-skills-definitions-detail"),
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
    *_main_chain_routes,
    *_agent_routes,
    *_orchestration_routes,
    *_model_routes,
    *_portal_routes,
    *_skills_routes,
]
