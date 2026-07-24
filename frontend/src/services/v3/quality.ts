import { http } from '@/services/http'
import type {
  CommandRunSummary,
  QualityFindingSource,
  QualityState,
} from '@/types/v3/domain'

function qualityBase(projectId: string): string {
  return `/api/v3/projects/${projectId}/quality/`
}

export type QualityCommandResult = {
  command_run: CommandRunSummary
}

export type QualityAcceptFindingItem = {
  source: QualityFindingSource
  finding_key: string
  title?: string
  severity?: string
}

export type QualityAcceptBody = {
  findings: QualityAcceptFindingItem[]
}

export type QualityReviseBody = {
  finding_keys?: string[]
  episode_range?: { start: number; end: number }
}

export async function getQualityState(projectId: string): Promise<QualityState> {
  return http.get<QualityState>(qualityBase(projectId))
}

export async function scoreQuality(projectId: string): Promise<QualityCommandResult> {
  return http.post<QualityCommandResult>(`${qualityBase(projectId)}score/`, {})
}

export async function checkCompliance(projectId: string): Promise<QualityCommandResult> {
  return http.post<QualityCommandResult>(`${qualityBase(projectId)}compliance/`, {})
}

export async function acceptFindings(
  projectId: string,
  body: QualityAcceptBody,
): Promise<QualityCommandResult> {
  return http.post<QualityCommandResult>(`${qualityBase(projectId)}accept/`, body)
}

export async function reviseFromFindings(
  projectId: string,
  body?: QualityReviseBody,
): Promise<QualityCommandResult> {
  return http.post<QualityCommandResult>(`${qualityBase(projectId)}revise/`, body ?? {})
}
