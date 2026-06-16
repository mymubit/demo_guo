import { adminRequest } from './http'

export const adminOrchestration = {
  getFlowBlueprint: () => adminRequest('GET', '/api/admin/orchestration/flow/blueprint/'),
  patchFlowStep: (stepId, data) =>
    adminRequest('PUT', `/api/admin/orchestration/flow/steps/${stepId}/`, { data }),
  reorderFlowSteps: (orderedIds) =>
    adminRequest('PUT', '/api/admin/orchestration/flow/steps/reorder/', {
      data: { ordered_ids: orderedIds },
    }),
  patchFlowRegistryMeta: (data) =>
    adminRequest('PUT', '/api/admin/orchestration/flow/registry-meta/', { data }),
  publishFlowBlueprint: (data = {}) =>
    adminRequest('POST', '/api/admin/orchestration/flow/publish/', { data }),
  recentRuns: (limit = 40) =>
    adminRequest('GET', `/api/admin/orchestration/recent-runs/?limit=${limit}`),
  stats: (limit = 300) =>
    adminRequest('GET', `/api/admin/orchestration/stats/?limit=${limit}`),
  projectTraces: (projectId) =>
    adminRequest('GET', `/api/admin/orchestration/projects/${projectId}/traces/`),
  executionRun: (runId) =>
    adminRequest('GET', `/api/admin/orchestration/execution-runs/${runId}/`),
}
