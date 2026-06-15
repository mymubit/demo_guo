import { adminRequest } from './http'

export const adminMainChain = {
  getBlueprint: () => adminRequest('GET', '/api/admin/main-chain/blueprint/'),
  patchStep: (stepId, data) =>
    adminRequest('PUT', `/api/admin/main-chain/steps/${stepId}/`, { data }),
  patchRegistryMeta: (data) =>
    adminRequest('PUT', '/api/admin/main-chain/registry-meta/', { data }),
}
