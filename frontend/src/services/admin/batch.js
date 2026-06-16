/**
 * admin/batch.js —— 批量创作 + 素材库 + 规则进化 API
 */
import { adminRequest, unwrapAdminList } from './http'

export const adminBatch = {
  listJobs: (params) =>
    adminRequest('GET', '/api/admin/creation/batch/', { params }).then(unwrapAdminList),
  createJob: (data) =>
    adminRequest('POST', '/api/admin/creation/batch/', { data }),
  getJob: (id) =>
    adminRequest('GET', `/api/admin/creation/batch/${id}/`),
  dispatchJob: (id) =>
    adminRequest('POST', `/api/admin/creation/batch/${id}/dispatch/`),
  pauseJob: (id) =>
    adminRequest('POST', `/api/admin/creation/batch/${id}/pause/`),
  resumeJob: (id) =>
    adminRequest('POST', `/api/admin/creation/batch/${id}/resume/`),
  retryItem: (batchId, itemId) =>
    adminRequest('POST', `/api/admin/creation/batch/${batchId}/projects/${itemId}/retry/`),
}

export const adminLibrary = {
  list: (params) =>
    adminRequest('GET', '/api/admin/creation/library/materials/', { params }).then(unwrapAdminList),
  upload: (formData) =>
    adminRequest('POST', '/api/admin/creation/library/materials/', { data: formData }),
  getDetail: (id) =>
    adminRequest('GET', `/api/admin/creation/library/materials/${id}/`),
  parse: (id) =>
    adminRequest('POST', `/api/admin/creation/library/materials/${id}/parse/`),
  delete: (id) =>
    adminRequest('DELETE', `/api/admin/creation/library/materials/${id}/`),
}

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
