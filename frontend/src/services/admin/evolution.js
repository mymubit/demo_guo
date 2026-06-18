import { adminRequest, unwrapAdminList } from './http'

export const adminEvolution = {
  listProposals: (params) =>
    adminRequest('GET', '/api/admin/skills/evolution/', { params }).then(unwrapAdminList),
  analyze: (data) =>
    adminRequest('POST', '/api/admin/skills/evolution/analyze/', { data }),
  getProposal: (id) =>
    adminRequest('GET', `/api/admin/skills/evolution/${id}/`),
  approve: (id, comment) =>
    adminRequest('POST', `/api/admin/skills/evolution/${id}/approve/`, { data: { comment } }),
  reject: (id, comment) =>
    adminRequest('POST', `/api/admin/skills/evolution/${id}/reject/`, { data: { comment } }),
  apply: (id) =>
    adminRequest('POST', `/api/admin/skills/evolution/${id}/apply/`),
}
