/**
 * services/admin/operations.js —— 【运营 F2】运营监控中心服务
 *
 * 5 个核心方法 + 反馈/抽样管理：
 *  • dashboard(days)         - 主 Dashboard 聚合
 *  • contentQuality(days)    - 内容质量
 *  • feedback.list / .get / .patch / .remove / .summary
 *  • configHit(limit)        - 配置命中率
 *  • samples.list / .mark
 *  • behavior.list(days, eventName, limit) - 行为事件列表
 */
import { adminRequest } from './http'
import { normalizeListResult } from '../adapters/listAdapter'

function withList(result) {
  return normalizeListResult(result)
}

export const adminOperations = {
  // 主 Dashboard
  dashboard: (params = {}) =>
    adminRequest('GET', '/api/admin/operations/dashboard/', { params }),

  // 内容质量
  contentQuality: (params = {}) =>
    adminRequest('GET', '/api/admin/operations/content-quality/', { params }),

  // 反馈管理
  feedback: {
    list: (params = {}) =>
      adminRequest('GET', '/api/admin/operations/feedback/', { params }).then(withList),
    summary: (params = {}) =>
      adminRequest('GET', '/api/admin/operations/feedback/summary/', { params }),
    get: (id) => adminRequest('GET', `/api/admin/operations/feedback/${id}/`),
    patch: (id, data) => adminRequest('PATCH', `/api/admin/operations/feedback/${id}/`, { data }),
    remove: (id) => adminRequest('DELETE', `/api/admin/operations/feedback/${id}/`),
  },

  // 配置命中率
  configHit: (params = {}) =>
    adminRequest('GET', '/api/admin/operations/config-hit/', { params }),

  // 抽样
  samples: {
    list: (params = {}) =>
      adminRequest('GET', '/api/admin/operations/samples/', { params }),
    mark: (projectIds = []) =>
      adminRequest('POST', '/api/admin/operations/samples/mark/', {
        data: { project_ids: projectIds },
      }),
  },

  // 行为事件
  behavior: {
    list: (params = {}) =>
      adminRequest('GET', '/api/admin/operations/behavior/', { params }),
  },
}

export default adminOperations
