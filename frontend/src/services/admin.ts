import { request } from './http'
import type { ConfigRollbackRequest, OpsConfigOverlay } from '@/types/domain'

const BASE = '/api/v1/drama/admin'

function withSlash(path: string): string {
  return path.endsWith('/') ? path : `${path}/`
}

export type LlmProviderItem = {
  id: string
  name: string
  base_url: string
  model_name: string
  api_key_set: boolean
  temperature: number
  max_tokens: number
  is_enabled: boolean
  is_active: boolean
  remark: string
  created_at?: string | null
  updated_at?: string | null
}

export type LlmProvidersResponse = {
  runtime: {
    status: string
    source: string
    model: string
    base_url: string
    api_key_set: boolean
  }
  providers: LlmProviderItem[]
}

export type LlmProviderWritePayload = {
  name: string
  base_url?: string
  model_name?: string
  api_key?: string
  temperature?: number
  max_tokens?: number
  is_enabled?: boolean
  is_active?: boolean
  remark?: string
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

  getLlmProviders() {
    return request<LlmProvidersResponse>('GET', withSlash(`${BASE}/llm/providers`))
  },

  createLlmProvider(data: LlmProviderWritePayload) {
    return request<LlmProviderItem>('POST', withSlash(`${BASE}/llm/providers`), { data })
  },

  updateLlmProvider(id: string, data: Partial<LlmProviderWritePayload>) {
    return request<LlmProviderItem>('PUT', withSlash(`${BASE}/llm/providers/${id}`), { data })
  },

  deleteLlmProvider(id: string) {
    return request<null>('DELETE', withSlash(`${BASE}/llm/providers/${id}`))
  },

  activateLlmProvider(id: string) {
    return request<LlmProviderItem>('POST', withSlash(`${BASE}/llm/providers/${id}/activate`))
  },

  testLlmProvider(id: string) {
    return request<{ ok: boolean; status_code?: number; detail?: string; error?: string }>(
      'POST',
      withSlash(`${BASE}/llm/providers/${id}/test`),
    )
  },
}
