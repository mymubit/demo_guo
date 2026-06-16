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
  duplicateFusionPack: (sourcePackId, displayName, options = {}) =>
    adminRequest('POST', '/api/admin/main-chain/fusion/packs/', {
      data: {
        source_pack_id: sourcePackId,
        display_name: displayName,
        slug: options.slug || '',
        activate: options.activate ?? false,
      },
    }),
  updateFusionPack: (packId, data) =>
    adminRequest('PATCH', `/api/admin/main-chain/fusion/packs/${packId}/`, { data }),
  activateFusionPack: (packId) =>
    adminRequest('POST', `/api/admin/main-chain/fusion/packs/${packId}/activate/`),
  setDefaultFusionPack: (packId) =>
    adminRequest('POST', `/api/admin/main-chain/fusion/packs/${packId}/set-default/`),
  publishFusionPack: (packId, data = {}) =>
    adminRequest('POST', `/api/admin/main-chain/fusion/packs/${packId}/publish/`, { data }),
  getFusionMeta: () => adminRequest('GET', '/api/admin/main-chain/fusion/meta/'),
}
