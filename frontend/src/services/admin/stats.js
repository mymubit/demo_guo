/**
 * admin/stats.js —— 数据统计中心 API
 */
import { adminRequest } from './http'

export const adminStats = {
  kpi: () => adminRequest('GET', '/api/admin/stats/kpi/'),
  trend: (params = {}) => adminRequest('GET', '/api/admin/stats/trend/', { params }),
  skillRanking: (params = {}) =>
    adminRequest('GET', '/api/admin/stats/skill-ranking/', { params }),
  failureRanking: (params = {}) =>
    adminRequest('GET', '/api/admin/stats/failure-ranking/', { params }),
  llmProviderUsage: (params = {}) =>
    adminRequest('GET', '/api/admin/stats/llm-provider-usage/', { params }),
  nodeDuration: (params = {}) =>
    adminRequest('GET', '/api/admin/stats/node-duration/', { params }),
}
