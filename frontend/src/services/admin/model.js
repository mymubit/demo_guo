import { adminRequest, unwrapAdminListData } from './http'

export const adminModel = {
  getLlm: () => adminRequest('GET', '/api/admin/model/llm/'),
  updateGlobalSettings: (data) => adminRequest('PUT', '/api/admin/model/llm/settings/', { data }),
  createProvider: (data) => adminRequest('POST', '/api/admin/model/llm/providers/', { data }),
  updateProvider: (id, data) =>
    adminRequest('PUT', `/api/admin/model/llm/providers/${id}/`, { data }),
  deleteProvider: (id) => adminRequest('DELETE', `/api/admin/model/llm/providers/${id}/`),
  activateProvider: (id) =>
    adminRequest('POST', `/api/admin/model/llm/providers/${id}/activate/`),
  testLlm: (data) => adminRequest('POST', '/api/admin/model/llm/test/', { data: data || {} }),
  syncPresets: () => adminRequest('POST', '/api/admin/model/llm/presets/sync/'),
  getRoutingPlan: () => adminRequest('GET', '/api/admin/model/llm/routing-plan/'),
  setupFromEnv: (data = {}) => adminRequest('POST', '/api/admin/model/llm/env-setup/', { data }),
  listCatalog: () =>
    adminRequest('GET', '/api/admin/model/llm/catalog/').then(unwrapAdminListData),
  createCatalog: (data) => adminRequest('POST', '/api/admin/model/llm/catalog/', { data }),
  updateCatalog: (id, data) =>
    adminRequest('PUT', `/api/admin/model/llm/catalog/${id}/`, { data }),
  deleteCatalog: (id) => adminRequest('DELETE', `/api/admin/model/llm/catalog/${id}/`),
  recalculateUsageCosts: () =>
    adminRequest('POST', '/api/admin/model/llm/usage/recalculate/'),
  updateVendorCredential: (vendor, data) =>
    adminRequest(
      'PUT',
      `/api/admin/model/llm/vendors/${encodeURIComponent(vendor)}/credential/`,
      { data }
    ),
}
