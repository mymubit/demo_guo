import { request, API_BASE_URL, getAccessToken } from './http'
import {
  normalizeCreationProgress,
  normalizeCreationSubmitResult,
} from './adapters/businessAdapters'

export const creation = {
  async submit(payload) {
    const data = await request('POST', '/api/creation/submit/', { data: payload })
    return normalizeCreationSubmitResult(data)
  },
  workspace(projectId) {
    return request('GET', `/api/creation/projects/${projectId}/workspace/`)
  },
  estimateAgent(projectId, agentId, params = {}) {
    return request('POST', `/api/creation/projects/${projectId}/agents/${agentId}/estimate/`, {
      data: { params },
    })
  },
  runAgent(projectId, agentId, params = {}) {
    return request('POST', `/api/creation/projects/${projectId}/agents/${agentId}/run/`, {
      data: { params },
    })
  },
  agentRuns(projectId, agentId) {
    return request('GET', `/api/creation/projects/${projectId}/agents/${agentId}/runs/`)
  },
  runDetail(projectId, runId) {
    return request('GET', `/api/creation/projects/${projectId}/runs/${runId}/`)
  },
  artifact(projectId, artifactKey) {
    return request('GET', `/api/creation/projects/${projectId}/artifacts/${artifactKey}/`)
  },
  listChunks(projectId, { kind = 'episode_scripts', limit = 50, offset = 0 } = {}) {
    return request('GET', `/api/creation/projects/${projectId}/chunks/`, {
      params: { kind, limit, offset },
    })
  },
  agentNotes(projectId) {
    return request('GET', `/api/creation/projects/${projectId}/agent-notes/`)
  },
  patchAgentNotes(projectId, agentNotes) {
    return request('PATCH', `/api/creation/projects/${projectId}/agent-notes/`, {
      data: { agent_notes: agentNotes },
    })
  },
  /**
   * SSE 流式 Agent（返回原始 Response，供 useSkillStream 或自定义消费）
   */
  async streamAgent(projectId, agentId, params = {}, { signal } = {}) {
    const token = getAccessToken()
    const url = `${API_BASE_URL}/api/creation/projects/${projectId}/agents/${agentId}/stream/`
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ params }),
      signal,
    })
  },
  async continueChunks(projectId, { agentId = 'script', toEpisode, params = {} } = {}, options = {}) {
    const token = getAccessToken()
    const url = `${API_BASE_URL}/api/creation/projects/${projectId}/chunks/continue/`
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        agent_id: agentId,
        to_episode: toEpisode,
        params,
      }),
      signal: options.signal,
    })
  },
  async progress(projectId) {
    const data = await request('GET', `/api/creation/progress/${projectId}/`)
    return normalizeCreationProgress(data)
  },
  fusionCatalog() {
    return request('GET', '/api/creation/fusion/catalog/')
  },
  agentCatalog() {
    return request('GET', '/api/creation/agents/catalog/')
  },
  workspaceCatalog() {
    return request('GET', '/api/creation/agents/workspace-catalog/')
  },
  fusionNodes(packId) {
    const suffix = packId ? `?pack_id=${encodeURIComponent(packId)}` : ''
    return request('GET', `/api/creation/fusion/nodes/${suffix}`)
  },
  aiGenerate(actionKey, context = {}) {
    return request('POST', '/api/creation/ai/generate/', {
      data: { action_key: actionKey, context },
    })
  },
  download(projectId, format) {
    return request('GET', `/api/creation/download/${projectId}/`, {
      params: format ? { format } : undefined,
      responseType: 'blob',
    })
  },
  share(projectId, options) {
    return request('POST', `/api/creation/share/${projectId}/`, { data: options || {} })
  },
  shareView(token) {
    return request('GET', `/api/creation/share/view/${token}/`)
  },
  dlByToken(token, format) {
    return request('GET', `/api/creation/dl/${token}/`, {
      params: format ? { format } : undefined,
      responseType: 'blob',
    })
  },
}
