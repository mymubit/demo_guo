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
import type { ThemeMatrix } from '@/types/workbench'

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

  getThemeMatrix() {
    return request<ThemeMatrix>('GET', withSlash(`${BASE}/theme-matrix`))
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

  getGenerationStatus(projectId: string, jobId: string) {
    return request<GenerationJob>(
      'GET',
      withSlash(`${BASE}/projects/${projectId}/generation/${jobId}`),
    )
  },

  getJob(jobId: string) {
    return request<GenerationJob>('GET', withSlash(`${BASE}/jobs/${jobId}`))
  },

  createExternalScriptReview(body: ExternalScriptReviewRequest | FormData) {
    const isForm = typeof FormData !== 'undefined' && body instanceof FormData
    return request<GenerationJob>('POST', withSlash(`${BASE}/external-script-reviews`), {
      data: body,
      headers: isForm ? {} : { 'Content-Type': 'application/json' },
    })
  },
}
