import { request } from './http'
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
  fusionSnapshot(projectId) {
    return request('GET', `/api/creation/fusion/${projectId}/`)
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
