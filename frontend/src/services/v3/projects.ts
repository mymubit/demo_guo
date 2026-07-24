import { http } from '@/services/http'
import type {
  CommandRunSummary,
  CreateProjectRequest,
  ProjectSummary,
} from '@/types/v3/domain'

const PROJECTS_BASE = '/api/v3/projects/'

type ProjectListResponse = {
  items: ProjectSummary[]
}

export type DispatchCommandInput = {
  command_type: string
  payload: Record<string, unknown>
  idempotency_key?: string
}

export type DispatchCommandResult = {
  command_run: CommandRunSummary
  project?: ProjectSummary
}

export async function listProjects(includeArchived?: boolean): Promise<ProjectSummary[]> {
  const options = includeArchived ? { params: { include_archived: 1 } } : undefined
  const data = await http.get<ProjectListResponse>(PROJECTS_BASE, options)
  return data.items
}

export async function createProject(body: CreateProjectRequest): Promise<ProjectSummary> {
  return http.post<ProjectSummary>(PROJECTS_BASE, body)
}

export async function getProject(id: string): Promise<ProjectSummary> {
  return http.get<ProjectSummary>(`${PROJECTS_BASE}${id}/`)
}

export async function archiveProject(id: string): Promise<ProjectSummary> {
  return http.post<ProjectSummary>(`${PROJECTS_BASE}${id}/archive/`)
}

export async function deleteProject(id: string): Promise<{ deleted: boolean; id: string }> {
  return http.delete<{ deleted: boolean; id: string }>(`${PROJECTS_BASE}${id}/`)
}

export async function dispatchCommand(input: DispatchCommandInput): Promise<DispatchCommandResult> {
  return http.post<DispatchCommandResult>('/api/v3/commands/', input)
}
