import { adminRequest, normalizeWorkflowSteps, normalizeFusionPacks } from './http'

export const adminWorkflow = {
  listSteps: () =>
    adminRequest('GET', '/api/admin/main-chain/steps/').then(normalizeWorkflowSteps),
  updateStep: (id, data) =>
    adminRequest('PUT', `/api/admin/main-chain/steps/${id}/`, { data }),
  syncSteps: () => adminRequest('POST', '/api/admin/main-chain/steps/sync/'),
  importFusionPipeline: (data) =>
    adminRequest('POST', '/api/admin/main-chain/fusion/import/', { data: data || {} }),
  listFusionPacks: () =>
    adminRequest('GET', '/api/admin/main-chain/fusion/packs/').then(normalizeFusionPacks),
  activateFusionPack: (packId) =>
    adminRequest('POST', `/api/admin/main-chain/fusion/packs/${packId}/activate/`),
  getFusionMeta: () => adminRequest('GET', '/api/admin/main-chain/fusion/meta/'),
}
