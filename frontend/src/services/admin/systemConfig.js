/**
 * admin/systemConfig.js —— 系统配置中心扩展 API（开关/阈值/配额/敏感词）
 */
import { adminRequest, unwrapAdminList } from './http'

export const adminSystemConfig = {
  getGlobalSwitches: () => adminRequest('GET', '/api/admin/system/global-switch/'),
  updateGlobalSwitches: (data) =>
    adminRequest('PUT', '/api/admin/system/global-switch/', { data }),

  getThresholds: () => adminRequest('GET', '/api/admin/system/thresholds/'),
  updateThresholds: (data) => adminRequest('PUT', '/api/admin/system/thresholds/', { data }),

  getQuotaRules: () => adminRequest('GET', '/api/admin/system/quota-rules/'),
  updateQuotaRules: (data) =>
    adminRequest('PUT', '/api/admin/system/quota-rules/', { data }),

  listSensitiveWords: (params = {}) =>
    adminRequest('GET', '/api/admin/system/sensitive-words/', { params }).then(unwrapAdminList),
  importSensitiveWords: (data) =>
    adminRequest('POST', '/api/admin/system/sensitive-words/', { data }),
}
