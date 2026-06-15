import { adminRequest } from './http'

export const adminOrchestration = {
  stats: (limit = 300) =>
    adminRequest('GET', `/api/admin/orchestration/stats/?limit=${limit}`),
  projectTraces: (projectId) =>
    adminRequest('GET', `/api/admin/orchestration/projects/${projectId}/traces/`),
  executionRun: (runId) =>
    adminRequest('GET', `/api/admin/orchestration/execution-runs/${runId}/`),
}
