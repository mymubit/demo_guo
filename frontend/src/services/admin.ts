import { request } from './http'
import type { ConfigRollbackRequest, OpsConfigOverlay } from '@/types/domain'

const BASE = '/api/v1/drama/admin'

function withSlash(path: string): string {
  return path.endsWith('/') ? path : `${path}/`
}

export const adminApi = {
  getConfig() {
    return request<OpsConfigOverlay>('GET', withSlash(`${BASE}/config`))
  },

  updateConfig(data: OpsConfigOverlay, etagRevision: number) {
    return request<OpsConfigOverlay>('PUT', withSlash(`${BASE}/config`), {
      data,
      headers: { 'If-Match': String(etagRevision) },
    })
  },

  rollback(body: ConfigRollbackRequest) {
    return request<OpsConfigOverlay>('POST', withSlash(`${BASE}/config/rollback`), { data: body })
  },
}
