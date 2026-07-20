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
    return request<{
      ok: boolean
      status_code?: number
      latency_ms?: number
      probe?: string
      detail?: string
      error?: string
      message?: string
    }>('POST', withSlash(`${BASE}/llm/providers/${id}/test`))
  },

  getLlmLogs(params?: {
    project_id?: string
    job_id?: string
    role?: string
    status?: string
    limit?: number
  }) {
    const qs = new URLSearchParams()
    if (params?.project_id) qs.set('project_id', params.project_id)
    if (params?.job_id) qs.set('job_id', params.job_id)
    if (params?.role) qs.set('role', params.role)
    if (params?.status) qs.set('status', params.status)
    if (params?.limit) qs.set('limit', String(params.limit))
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request<LlmCallLogsResponse>('GET', `${withSlash(`${BASE}/llm/logs`)}${suffix}`)
  },

  getLlmLogDetail(id: string) {
    return request<LlmCallLogDetail>('GET', withSlash(`/api/v1/drama/llm-logs/${id}`))
  },

  getSkillOpsOverview(params?: { limit?: number; role?: string }) {
    const qs = new URLSearchParams()
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.role) qs.set('role', params.role)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request<SkillOpsOverview>('GET', `${withSlash(`${BASE}/skill-ops`)}${suffix}`)
  },

  exportSkillFailures(params?: { limit?: number; role?: string }) {
    const qs = new URLSearchParams()
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.role) qs.set('role', params.role)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request<SkillOpsExportResponse>(
      'GET',
      `${withSlash(`${BASE}/skill-ops/export`)}${suffix}`,
    )
  },
}

export type LlmCallLogItem = {
  id: string
  project_id: string | null
  project_title?: string | null
  job_id: string | null
  job_status?: string | null
  job_error_message?: string | null
  actor: string
  role: string
  role_label?: string | null
  purpose: string
  status: 'success' | 'error' | string
  model_name: string
  base_url: string
  latency_ms: number
  http_status: number | null
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
  error_message: string | null
  seq_in_job: number
  created_at: string | null
  system_prompt_preview: string | null
  user_prompt_preview: string | null
  response_preview: string | null
  injection_system_chars?: number | null
  injection_truncated?: boolean | null
}

export type InjectionManifest = {
  version: number
  agent_id: string
  bundle_version?: string
  built_at?: string
  layers: Record<string, { chars: number; truncated?: boolean }>
  modules?: {
    included?: Array<{ id: string; label_zh?: string; chars?: number; mode?: string }>
    skipped?: Array<{ id: string; label_zh?: string; reason?: string; chars?: number }>
  }
  knowledge?: {
    included?: Array<{ path: string; chars?: number; mode?: string }>
    skipped?: Array<{ path: string; reason?: string; chars?: number }>
  }
  rules?: {
    sections_included?: string[]
    item_count?: number
    truncated?: boolean
    max_chars?: number
  }
  policies?: {
    evaluate_enable_when?: boolean
    module_max_chars?: number
    rule_max_chars?: number
    knowledge_max_chars?: number
    module_as_index?: boolean
  }
  system_chars?: number
  user_chars?: number
  checksum?: string
}

export type LlmCallLogDetail = LlmCallLogItem & {
  system_prompt: string
  user_prompt: string
  response_text: string
  response_body: unknown
  provider_request_id: string | null
  injection_manifest?: InjectionManifest | null
}

export type LlmCallLogsResponse = {
  items: LlmCallLogItem[]
  count: number
}

export type SkillFailureItem = {
  id: string
  created_at: string | null
  role: string
  purpose: string
  status: string
  category?: string
  error_message: string | null
  model_name: string
  project_id: string | null
  job_id: string | null
  response_preview: string
  suggested_anti_example?: {
    id: string
    severity: string
    title: string
    note: string
    raw_error: string | null
  } | null
}

export type SkillOpsOverview = {
  failures: SkillFailureItem[]
  failure_count: number
  noise_counts?: {
    provider_config: number
    infra: number
  }
  eval_summary: {
    total?: number
    passed?: number
    pass_rate?: number
    failed?: Array<{ id?: string; errors?: string[] }>
  } | null
  repair_stats: {
    sample_size: number
    repair_calls: number
    repair_success: number
    repair_success_rate: number | null
    failure_like_count?: number
  }
  purpose?: string
  hints?: {
    anti_examples: string
    eval_cli: string
    validate_cli: string
  }
}

export type SkillOpsExportResponse = {
  items: SkillFailureItem[]
  count: number
}
