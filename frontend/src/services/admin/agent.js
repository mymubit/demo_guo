import { adminRequest, normalizeAgentRegistry, normalizeAgentLlmRoutes } from './http'

function unwrapData(res) {
  return res?.data?.data ?? res?.data ?? res
}

export const adminAgent = {
  getRegistry: () =>
    adminRequest('GET', '/api/admin/agent/registry/').then((res) => normalizeAgentRegistry(unwrapData(res))),
  saveRegistry: (data) => adminRequest('PUT', '/api/admin/agent/registry/', { data }),
  catalog: () => adminRequest('GET', '/api/admin/agent/catalog/').then(unwrapData),
  listLlmRoutes: () =>
    adminRequest('GET', '/api/admin/agent/llm-routes/').then((res) => normalizeAgentLlmRoutes(unwrapData(res))),
  saveLlmRoute: (data) => adminRequest('POST', '/api/admin/agent/llm-routes/', { data }),
  updateLlmRoute: (id, data) =>
    adminRequest('PUT', `/api/admin/agent/llm-routes/${id}/`, { data }),
  seedLlmRoutes: () => adminRequest('POST', '/api/admin/agent/llm-routes/seed/'),
  getReviewScoring: () => adminRequest('GET', '/api/admin/agent/review-scoring/').then(unwrapData),
  saveReviewScoring: (data) => adminRequest('PUT', '/api/admin/agent/review-scoring/', { data }),

  listDefinitions: () =>
    adminRequest('GET', '/api/admin/agent/definitions/').then((res) => unwrapData(res)?.agents || []),
  getDefinition: (agentId) =>
    adminRequest('GET', `/api/admin/agent/definitions/${agentId}/`).then((res) => unwrapData(res)?.agent || unwrapData(res)),
  saveDefinition: (agentId, data) =>
    adminRequest('PUT', `/api/admin/agent/definitions/${agentId}/`, { data }),
  listPrompts: (agentId) =>
    adminRequest('GET', `/api/admin/agent/definitions/${agentId}/prompts/`).then((res) => unwrapData(res)?.prompts || []),
  savePrompt: (agentId, data) =>
    adminRequest('POST', `/api/admin/agent/definitions/${agentId}/prompts/`, { data }),
  activatePrompt: (agentId, version) =>
    adminRequest('POST', `/api/admin/agent/definitions/${agentId}/prompts/${version}/activate/`),
  listKnowledge: () =>
    adminRequest('GET', '/api/admin/agent/knowledge/').then((res) => unwrapData(res)?.knowledge || []),
  saveKnowledge: (data) =>
    adminRequest('POST', '/api/admin/agent/knowledge/', { data }),
  listBindings: (agentId) =>
    adminRequest('GET', `/api/admin/agent/definitions/${agentId}/knowledge-bindings/`).then((res) => unwrapData(res)?.bindings || []),
  saveBinding: (agentId, data) =>
    adminRequest('POST', `/api/admin/agent/definitions/${agentId}/knowledge-bindings/`, { data }),
  deleteBinding: (agentId, bindingId) =>
    adminRequest('DELETE', `/api/admin/agent/definitions/${agentId}/knowledge-bindings/${bindingId}/`),
  getKnowledge: (knowledgeId) =>
    adminRequest('GET', `/api/admin/agent/knowledge/${knowledgeId}/`).then((res) => unwrapData(res)?.knowledge || unwrapData(res)),
  deleteKnowledge: (knowledgeId) =>
    adminRequest('DELETE', `/api/admin/agent/knowledge/${knowledgeId}/`),
  listAgentRuns: (params = {}) => {
    const query = new URLSearchParams()
    if (params.agentId) query.set('agent_id', params.agentId)
    if (params.limit) query.set('limit', String(params.limit))
    const suffix = query.toString() ? `?${query.toString()}` : ''
    return adminRequest('GET', `/api/admin/agent/runs/${suffix}`).then((res) => unwrapData(res)?.runs || [])
  },
  projectTraces: (projectId) =>
    adminRequest('GET', `/api/admin/agent/projects/${projectId}/traces/`).then(unwrapData),
  executionRun: (runId) =>
    adminRequest('GET', `/api/admin/agent/runs/${runId}/`).then(unwrapData),
}
