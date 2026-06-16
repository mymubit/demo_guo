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
  generateAgent(projectId, nodeIndex, options = {}) {
    return request('POST', `/api/creation/projects/${projectId}/agents/${nodeIndex}/generate/`, {
      data: {
        from_episode: options.from_episode,
        to_episode: options.to_episode,
        batch_size: options.batch_size,
        regenerate: options.regenerate,
        outline_mode: options.outline_mode,
        stage_key: options.stage_key,
      },
    })
  },
  acknowledgeQualityAlert(projectId, nodeIndex, alertCode) {
    return request('POST', `/api/creation/projects/${projectId}/agents/${nodeIndex}/quality-alert/ack/`, {
      data: { alert_code: alertCode },
    })
  },
  saveAgentContent(projectId, nodeIndex, data) {
    return request('PUT', `/api/creation/projects/${projectId}/agents/${nodeIndex}/content/`, {
      data,
    })
  },
  async progress(projectId) {
    const data = await request('GET', `/api/creation/progress/${projectId}/`)
    return normalizeCreationProgress(data)
  },
  confirmNode(projectId) {
    return request('POST', `/api/creation/projects/${projectId}/confirm/`)
  },
  regenerateNode(projectId, nodeIndex) {
    return request('POST', `/api/creation/projects/${projectId}/regenerate/`, {
      data: nodeIndex != null ? { node_index: nodeIndex } : {},
    })
  },
  fusionCatalog() {
    return request('GET', '/api/creation/fusion/catalog/')
  },
  agentCatalog() {
    return request('GET', '/api/creation/agents/catalog/')
  },
  fusionNodes(packId) {
    const suffix = packId ? `?pack_id=${encodeURIComponent(packId)}` : ''
    return request('GET', `/api/creation/fusion/nodes/${suffix}`)
  },
  fusionSnapshot(projectId) {
    return request('GET', `/api/creation/fusion/${projectId}/`)
  },
  nodePreview(projectId, nodeIndex) {
    return request('GET', `/api/creation/projects/${projectId}/nodes/${nodeIndex}/preview/`)
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
