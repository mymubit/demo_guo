import { adminRequest, normalizeAgentRegistry, normalizeAgentLlmRoutes } from './http'

export const adminAgent = {
  getRegistry: () =>
    adminRequest('GET', '/api/admin/agent/registry/').then(normalizeAgentRegistry),
  saveRegistry: (data) => adminRequest('PUT', '/api/admin/agent/registry/', { data }),
  importRegistry: (data) =>
    adminRequest('POST', '/api/admin/agent/registry/import/', { data: data || {} }),
  migrateRegistry: () => adminRequest('POST', '/api/admin/agent/registry/migrate/'),
  catalog: () => adminRequest('GET', '/api/admin/agent/catalog/'),
  listLlmRoutes: () =>
    adminRequest('GET', '/api/admin/agent/llm-routes/').then(normalizeAgentLlmRoutes),
  saveLlmRoute: (data) => adminRequest('POST', '/api/admin/agent/llm-routes/', { data }),
  updateLlmRoute: (id, data) =>
    adminRequest('PUT', `/api/admin/agent/llm-routes/${id}/`, { data }),
  seedLlmRoutes: () => adminRequest('POST', '/api/admin/agent/llm-routes/seed/'),
  getReviewScoring: () => adminRequest('GET', '/api/admin/agent/review-scoring/'),
  saveReviewScoring: (data) => adminRequest('PUT', '/api/admin/agent/review-scoring/', { data }),
}
