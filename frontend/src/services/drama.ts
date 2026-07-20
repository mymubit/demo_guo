import { request } from './http'
import type {
  ArtifactRecord,
  CreateProjectRequest,
  DramaProjectSummary,
  ExternalScriptReviewRequest,
  GenerationJob,
  GenerationStartRequest,
  ProjectSettings,
  StoryBibleApprovalRequest,
  WorkflowCommandRequest,
  WorkflowState,
} from '@/types/domain'
import type { WorkbenchFormApiResponse } from '@/types/workbench'
import type { LlmCallLogDetail, LlmCallLogsResponse } from '@/services/admin'

const BASE = '/api/v1/drama'

function withSlash(path: string): string {
  return path.endsWith('/') ? path : `${path}/`
}

export const dramaApi = {
  listProjects() {
    return request<DramaProjectSummary[]>('GET', withSlash(`${BASE}/projects`))
  },

  createProject(data: CreateProjectRequest) {
    return request<DramaProjectSummary>('POST', withSlash(`${BASE}/projects`), { data })
  },

  getProject(projectId: string) {
    return request<DramaProjectSummary>('GET', withSlash(`${BASE}/projects/${projectId}`))
  },

  deleteProject(projectId: string) {
    return request<null>('DELETE', withSlash(`${BASE}/projects/${projectId}`))
  },

  getSettings(projectId: string) {
    return request<ProjectSettings>('GET', withSlash(`${BASE}/projects/${projectId}/settings`))
  },

  updateSettings(projectId: string, data: ProjectSettings, etagRevision: number) {
    return request<ProjectSettings>('PUT', withSlash(`${BASE}/projects/${projectId}/settings`), {
      data,
      headers: { 'If-Match': String(etagRevision) },
    })
  },

  getWorkflow(projectId: string) {
    return request<WorkflowState>('GET', withSlash(`${BASE}/projects/${projectId}/workflow`))
  },

  postWorkflowCommand(projectId: string, body: WorkflowCommandRequest) {
    return request<WorkflowState>(
      'POST',
      withSlash(`${BASE}/projects/${projectId}/workflow/commands`),
      { data: body },
    )
  },

  approveStoryBible(projectId: string, body: StoryBibleApprovalRequest) {
    return request<WorkflowState>(
      'POST',
      withSlash(`${BASE}/projects/${projectId}/approvals/story-bible`),
      { data: body },
    )
  },

  getArtifact<T = unknown>(projectId: string, artifactKey: string) {
    return request<ArtifactRecord<T>>(
      'GET',
      withSlash(`${BASE}/projects/${projectId}/artifacts/${artifactKey}`),
    )
  },

  /** Runtime workbench form definition (stages / modules / parameter fields). No static fallback. */
  getWorkbenchForm() {
    return request<WorkbenchFormApiResponse>(
      'GET',
      withSlash(`${BASE}/meta/workbench-form`),
    )
  },

  startGeneration(
    projectId: string,
    body: GenerationStartRequest,
  ) {
    return request<GenerationJob>(
      'POST',
      withSlash(`${BASE}/projects/${projectId}/generation/start`),
      { data: body },
    )
  },

  getLatestGeneration(
    projectId: string,
    params?: { role?: string; artifact_key?: string },
  ) {
    const qs = new URLSearchParams()
    if (params?.role) qs.set('role', params.role)
    if (params?.artifact_key) qs.set('artifact_key', params.artifact_key)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request<GenerationJob | null>(
      'GET',
      `${withSlash(`${BASE}/projects/${projectId}/generation/latest`)}${suffix}`,
    )
  },

  getGenerationStatus(projectId: string, jobId: string) {
    return request<GenerationJob>(
      'GET',
      withSlash(`${BASE}/projects/${projectId}/generation/${jobId}`),
    )
  },

  abandonGeneration(projectId: string, jobId: string) {
    return request<GenerationJob>(
      'POST',
      withSlash(`${BASE}/projects/${projectId}/generation/${jobId}/abandon`),
    )
  },

  getJob(jobId: string) {
    return request<GenerationJob>('GET', withSlash(`${BASE}/jobs/${jobId}`))
  },

  deleteJob(jobId: string) {
    return request<{ deleted: boolean; job_id: string }>(
      'DELETE',
      withSlash(`${BASE}/jobs/${jobId}`),
    )
  },

  reprocessJob(jobId: string) {
    return request<GenerationJob>('POST', withSlash(`${BASE}/jobs/${jobId}/reprocess`))
  },

  createExternalScriptReview(body: ExternalScriptReviewRequest | FormData) {
    const isForm = typeof FormData !== 'undefined' && body instanceof FormData
    return request<GenerationJob>('POST', withSlash(`${BASE}/external-script-reviews`), {
      data: body,
      // FormData 勿手动设 Content-Type，交由 http 拦截器清除默认 json
      headers: isForm ? undefined : { 'Content-Type': 'application/json' },
    })
  },

  listExternalScriptReviews(params?: { limit?: number }) {
    const qs = new URLSearchParams()
    if (params?.limit) qs.set('limit', String(params.limit))
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request<{ items: GenerationJob[]; total: number }>(
      'GET',
      `${withSlash(`${BASE}/external-script-reviews`)}${suffix}`,
    )
  },

  getJobLlmLogs(jobId: string, params?: { role?: string; limit?: number; detail?: boolean }) {
    const qs = new URLSearchParams()
    if (params?.role) qs.set('role', params.role)
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.detail === false) qs.set('detail', '0')
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request<LlmCallLogsResponse>(
      'GET',
      `${withSlash(`${BASE}/jobs/${jobId}/llm-logs`)}${suffix}`,
    )
  },

  getProjectLlmLogs(
    projectId: string,
    params?: { job_id?: string; role?: string; limit?: number },
  ) {
    const qs = new URLSearchParams()
    if (params?.job_id) qs.set('job_id', params.job_id)
    if (params?.role) qs.set('role', params.role)
    if (params?.limit) qs.set('limit', String(params.limit))
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request<LlmCallLogsResponse>(
      'GET',
      `${withSlash(`${BASE}/projects/${projectId}/llm-logs`)}${suffix}`,
    )
  },

  getLlmLogDetail(logId: string) {
    return request<LlmCallLogDetail>('GET', withSlash(`${BASE}/llm-logs/${logId}`))
  },
}
