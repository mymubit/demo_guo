import { adminRequest, unwrapAdminList } from './http'

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
