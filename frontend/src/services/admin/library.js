import { adminRequest, unwrapAdminList } from './http'

export const adminLibrary = {
  list: (params) =>
    adminRequest('GET', '/api/admin/creation/library/materials/', { params }).then(unwrapAdminList),
  upload: (formData, { onUploadProgress } = {}) =>
    adminRequest('POST', '/api/admin/creation/library/materials/upload/', {
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    }),
  getDetail: (id) =>
    adminRequest('GET', `/api/admin/creation/library/materials/${id}/`),
  parse: (id) =>
    adminRequest('POST', `/api/admin/creation/library/materials/${id}/parse/`),
  delete: (id) =>
    adminRequest('DELETE', `/api/admin/creation/library/materials/${id}/`),
}
