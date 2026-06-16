import { adminRequest } from './http'
import { normalizeListResult } from '../adapters/listAdapter'

function withListFallback(result) {
  return normalizeListResult(result)
}

export const adminMonitoring = {
  overview: (params = {}) => adminRequest('GET', '/api/admin/monitoring/overview/', { params }),
  health: () => adminRequest('GET', '/api/admin/monitoring/health/'),
  frontendEvents: (params = {}) =>
    adminRequest('GET', '/api/admin/monitoring/frontend-events/', { params }).then(withListFallback),
  exceptions: (params = {}) =>
    adminRequest('GET', '/api/admin/monitoring/exceptions/', { params }).then(withListFallback),
  apiPerformance: (params = {}) =>
    adminRequest('GET', '/api/admin/monitoring/api-performance/', { params }).then(withListFallback),
  slowSql: (params = {}) =>
    adminRequest('GET', '/api/admin/monitoring/slow-sql/', { params }).then(withListFallback),
  alertRules: (params = {}) =>
    adminRequest('GET', '/api/admin/monitoring/alert-rules/', { params }).then(withListFallback),
  createAlertRule: (data) => adminRequest('POST', '/api/admin/monitoring/alert-rules/', { data }),
  updateAlertRule: (id, data) => adminRequest('PATCH', `/api/admin/monitoring/alert-rules/${id}/`, { data }),
  alertEvents: (params = {}) =>
    adminRequest('GET', '/api/admin/monitoring/alert-events/', { params }).then(withListFallback),
  maintenance: () => adminRequest('GET', '/api/admin/monitoring/maintenance/'),
  maintainData: (data) => adminRequest('POST', '/api/admin/monitoring/maintenance/', { data }),
}
