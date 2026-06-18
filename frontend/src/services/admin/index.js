/**
 * admin/index.js —— 后台管理 API 聚合
 */
import { adminRequest, unwrapAdminList, unwrapAdminListData } from './http'
import { adminAgent } from './agent'
import { adminModel } from './model'
import { adminMonitoring } from './monitoring'
import { adminSkill } from './skill'
import { adminStats } from './stats'
import { adminSystemConfig } from './systemConfig'
import { adminLibrary } from './library'
import { adminEvolution } from './evolution'
import { adminOperations } from './operations'

export {
  adminAgent,
  adminModel, adminMonitoring, adminSkill,
  adminStats, adminSystemConfig,
  adminLibrary, adminEvolution,
  adminOperations,
}

export const admin = {
  // 仪表盘
  getDashboard: () => adminRequest('GET', '/api/admin/dashboard/'),
  getStats: () => adminRequest('GET', '/api/admin/stats/summary/'),
  monitoring: adminMonitoring,
  // 【运营 F2】运营监控中心
  operations: adminOperations,

  // 用户
  listUsers: (params = {}) =>
    adminRequest('GET', '/api/admin/users/', { params }).then(unwrapAdminList),
  userRecentProjects: (userId) =>
    adminRequest('GET', `/api/admin/users/${userId}/recent_projects/`).then((res) => res?.data?.items ?? res?.items ?? []),
  toggleUserActive: (id) => adminRequest('POST', `/api/admin/users/${id}/toggle_active/`),
  resetUserPassword: (id, newPassword) =>
    adminRequest('POST', `/api/admin/users/${id}/reset_password/`, {
      data: newPassword ? { new_password: newPassword } : {},
    }),

  // 会员套餐
  listPlans: () =>
    adminRequest('GET', '/api/admin/members/plans/').then(unwrapAdminListData),
  createPlan: (data) => adminRequest('POST', '/api/admin/members/plans/', { data }),
  updatePlan: (id, data) =>
    adminRequest('PUT', `/api/admin/members/plans/${id}/`, { data }),
  deletePlan: (id) => adminRequest('DELETE', `/api/admin/members/plans/${id}/`),
  listPromoCodes: (limit = 50) =>
    adminRequest('GET', '/api/admin/members/codes/', { params: { limit } }).then(unwrapAdminListData),
  generatePromo: (data) =>
    adminRequest('POST', '/api/admin/members/codes/generate/', { data }),

  // 订单
  listOrders: (params = {}) =>
    adminRequest('GET', '/api/admin/orders/', { params }).then(unwrapAdminList),
  refundOrder: (id) => adminRequest('POST', `/api/admin/orders/${id}/refund/`),

  // 门户配置
  getSkillConfigs: () =>
    adminRequest('GET', '/api/admin/portal/configs/').then(unwrapAdminListData),
  updateSkillConfig: (key, value) =>
    adminRequest('PUT', `/api/admin/portal/configs/${encodeURIComponent(key)}/`, {
      data: { value },
    }),
  getThemes: () =>
    adminRequest('GET', '/api/admin/portal/themes/').then(unwrapAdminListData),
  addTheme: (data) => adminRequest('POST', '/api/admin/portal/themes/', { data }),
  updateTheme: (id, data) =>
    adminRequest('PUT', `/api/admin/portal/themes/${id}/`, { data }),
  getHooks: () =>
    adminRequest('GET', '/api/admin/portal/hooks/').then(unwrapAdminListData),
  addHook: (data) => adminRequest('POST', '/api/admin/portal/hooks/', { data }),
  updateHook: (id, data) =>
    adminRequest('PUT', `/api/admin/portal/hooks/${id}/`, { data }),
  deleteHook: (id) => adminRequest('DELETE', `/api/admin/portal/hooks/${id}/`),
  getCreationFormCatalog: () => adminRequest('GET', '/api/admin/portal/creation-form/'),
  saveCreationFormCatalog: (overrides) =>
    adminRequest('PUT', '/api/admin/portal/creation-form/', { data: { overrides } }),
  importCreationFormFromDisk: (data) =>
    adminRequest('POST', '/api/admin/portal/creation-form/import/', { data: data || {} }),

  // 系统设置
  getSystemSettings: () => adminRequest('GET', '/api/admin/system/settings/'),
  clearCache: () => adminRequest('POST', '/api/admin/system/cache/clear/'),
  listSystemConfigCategories: () =>
    adminRequest('GET', '/api/admin/system/config-categories/').then(unwrapAdminListData),
  createSystemConfigCategory: (data) =>
    adminRequest('POST', '/api/admin/system/config-categories/', { data }),
  updateSystemConfigCategory: (id, data) =>
    adminRequest('PATCH', `/api/admin/system/config-categories/${id}/`, { data }),
  deleteSystemConfigCategory: (id) =>
    adminRequest('DELETE', `/api/admin/system/config-categories/${id}/`),
  listSystemConfigs: (params = {}) =>
    adminRequest('GET', '/api/admin/system/configs/', { params }).then(unwrapAdminList),
  createSystemConfig: (data) =>
    adminRequest('POST', '/api/admin/system/configs/', { data }),
  updateSystemConfig: (id, data) =>
    adminRequest('PATCH', `/api/admin/system/configs/${id}/`, { data }),
  deleteSystemConfig: (id, data = {}) =>
    adminRequest('DELETE', `/api/admin/system/configs/${id}/`, { data }),
  toggleSystemConfig: (id, data = {}) =>
    adminRequest('POST', `/api/admin/system/configs/${id}/toggle/`, { data }),
  bulkUpdateSystemConfigs: (data) =>
    adminRequest('POST', '/api/admin/system/configs/bulk-update/', { data }),
  refreshSystemConfigCache: () =>
    adminRequest('POST', '/api/admin/system/configs/refresh-cache/'),
  listSystemConfigAuditLogs: (params = {}) =>
    adminRequest('GET', '/api/admin/system/configs/audit-logs/', { params }).then(unwrapAdminList),

  // 计费
  getBillingSettings: () => adminRequest('GET', '/api/admin/billing/settings/'),
  updateBillingSettings: (data) =>
    adminRequest('PUT', '/api/admin/billing/settings/', { data }),
  listPricing: () =>
    adminRequest('GET', '/api/admin/billing/pricing/').then(unwrapAdminListData),
  savePricing: (data) => adminRequest('POST', '/api/admin/billing/pricing/', { data }),
  updatePricing: (id, data) =>
    adminRequest('PUT', `/api/admin/billing/pricing/${id}/`, { data }),
  listRechargePackages: () =>
    adminRequest('GET', '/api/admin/billing/recharge/').then(unwrapAdminListData),
  createRechargePackage: (data) =>
    adminRequest('POST', '/api/admin/billing/recharge/', { data }),
  updateRechargePackage: (id, data) =>
    adminRequest('PUT', `/api/admin/billing/recharge/${id}/`, { data }),
  deleteRechargePackage: (id) =>
    adminRequest('DELETE', `/api/admin/billing/recharge/${id}/`),
  listAiFieldPrompts: () =>
    adminRequest('GET', '/api/admin/billing/ai-prompts/').then(unwrapAdminListData),
  saveAiFieldPrompt: (data) =>
    adminRequest('POST', '/api/admin/billing/ai-prompts/', { data }),
  updateAiFieldPrompt: (id, data) =>
    adminRequest('PUT', `/api/admin/billing/ai-prompts/${id}/`, { data }),
  seedAiFieldPrompts: () =>
    adminRequest('POST', '/api/admin/billing/ai-prompts/seed/'),

  // LLM 模型（委托给 adminModel）
  getLlmConfig: () => adminModel.getLlm(),
  updateLlmGlobalSettings: (data) => adminModel.updateGlobalSettings(data),
  createLlmProvider: (data) => adminModel.createProvider(data),
  updateLlmProvider: (id, data) => adminModel.updateProvider(id, data),
  deleteLlmProvider: (id) => adminModel.deleteProvider(id),
  activateLlmProvider: (id) => adminModel.activateProvider(id),
  testLlmConfig: (data) => adminModel.testLlm(data),
  syncLlmPresets: () => adminModel.syncPresets(),
  getLlmRoutingPlan: () => adminModel.getRoutingPlan(),
  setupLlmFromEnv: (data = {}) => adminModel.setupFromEnv(data),
  listLlmCatalog: () => adminModel.listCatalog(),
  createLlmCatalog: (data) => adminModel.createCatalog(data),
  updateLlmCatalog: (id, data) => adminModel.updateCatalog(id, data),
  recalculateLlmUsageCosts: () => adminModel.recalculateUsageCosts(),
  updateLlmVendorCredential: (vendor, data) => adminModel.updateVendorCredential(vendor, data),
  deleteLlmCatalog: (id) => adminModel.deleteCatalog(id),

  // Agent（委托给 adminAgent）
  getAgentRegistryConfig: () => adminAgent.getRegistry(),
  saveAgentRegistryConfig: (data) => adminAgent.saveRegistry(data),
  listAgentLlmRoutes: () => adminAgent.listLlmRoutes(),
  saveAgentLlmRoute: (data) => adminAgent.saveLlmRoute(data),
  updateAgentLlmRoute: (id, data) => adminAgent.updateLlmRoute(id, data),
  seedAgentLlmRoutes: () => adminAgent.seedLlmRoutes(),
  agentCatalog: () => adminAgent.catalog(),
  getReviewScoringConfig: () => adminAgent.getReviewScoring(),
  saveReviewScoringConfig: (data) => adminAgent.saveReviewScoring(data),
  listIndependentAgents: () => adminAgent.listDefinitions(),
  getIndependentAgent: (agentId) => adminAgent.getDefinition(agentId),
  saveIndependentAgent: (agentId, data) => adminAgent.saveDefinition(agentId, data),
  listIndependentAgentPrompts: (agentId) => adminAgent.listPrompts(agentId),
  saveIndependentAgentPrompt: (agentId, data) => adminAgent.savePrompt(agentId, data),
  activateIndependentAgentPrompt: (agentId, version) => adminAgent.activatePrompt(agentId, version),
  listIndependentKnowledge: () => adminAgent.listKnowledge(),
  saveIndependentKnowledge: (data) => adminAgent.saveKnowledge(data),
  listIndependentAgentBindings: (agentId) => adminAgent.listBindings(agentId),
  saveIndependentAgentBinding: (agentId, data) => adminAgent.saveBinding(agentId, data),
  deleteIndependentAgentBinding: (agentId, bindingId) => adminAgent.deleteBinding(agentId, bindingId),
  getIndependentKnowledge: (knowledgeId) => adminAgent.getKnowledge(knowledgeId),
  deleteIndependentKnowledge: (knowledgeId) => adminAgent.deleteKnowledge(knowledgeId),
  listIndependentAgentRuns: (params) => adminAgent.listAgentRuns(params),
  agentProjectTraces: (projectId) => adminAgent.projectTraces(projectId),
  agentExecutionRun: (runId) => adminAgent.executionRun(runId),

  // 创作中心
  listCreationProjects: (params = {}) =>
    adminRequest('GET', '/api/admin/creation/projects/', { params }).then(unwrapAdminList),
  deleteCreationProject: (projectId) =>
    adminRequest('DELETE', `/api/admin/creation/projects/${projectId}/`),

  // 技能规则
  listSkillRules: (params = {}) =>
    adminRequest('GET', '/api/admin/skills/rules/', { params }).then(unwrapAdminList),
  updateSkillRule: (id, data) =>
    adminRequest('PUT', `/api/admin/skills/rules/${id}/`, { data }),
  approveSkillRule: (id) => adminRequest('POST', `/api/admin/skills/rules/${id}/approve/`),
  archiveSkillRule: (id) => adminRequest('POST', `/api/admin/skills/rules/${id}/archive/`),
  importSkillRules: (data) =>
    adminRequest('POST', '/api/admin/skills/rules/import/', { data: data || {} }),

  // 会员功能矩阵
  listFeatureMatrix: () =>
    adminRequest('GET', '/api/admin/members/feature-matrix/').then(unwrapAdminListData),
  saveFeatureMatrixItem: (data) =>
    adminRequest('POST', '/api/admin/members/feature-matrix/', { data }),
  updateFeatureMatrixItem: (id, data) =>
    adminRequest('PUT', `/api/admin/members/feature-matrix/${id}/`, { data }),
  deleteFeatureMatrixItem: (id) =>
    adminRequest('DELETE', `/api/admin/members/feature-matrix/${id}/`),
  seedFeatureMatrix: () =>
    adminRequest('POST', '/api/admin/members/feature-matrix/seed/'),

  // 素材库
  library: () => adminLibrary.list(),
  libraryUpload: (formData) => adminLibrary.upload(formData),
  libraryParse: (id) => adminLibrary.parse(id),

  // 规则进化
  evolutionProposals: (params) => adminEvolution.listProposals(params),
  evolutionAnalyze: (data) => adminEvolution.analyze(data),
  evolutionApprove: (id, comment) => adminEvolution.approve(id, comment),
  evolutionReject: (id, comment) => adminEvolution.reject(id, comment),
  evolutionApply: (id) => adminEvolution.apply(id),
}
