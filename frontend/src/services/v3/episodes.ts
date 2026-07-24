import { http } from '@/services/http'
import type { CommandRunSummary, EpisodesState } from '@/types/v3/domain'

function episodesBase(projectId: string): string {
  return `/api/v3/projects/${projectId}/episodes/`
}

export type EpisodesCommandResult = {
  command_run: CommandRunSummary
}

export type EpisodeGenerateBody = {
  episode_count?: number
  duration_target?: string
  planning_requests?: Record<string, unknown>
}

export type EpisodeReviseBody = {
  episode_numbers: number[]
  revision_requests?: Record<string, unknown>
}

export async function getEpisodesState(projectId: string): Promise<EpisodesState> {
  return http.get<EpisodesState>(episodesBase(projectId))
}

export async function generateEpisodePlan(
  projectId: string,
  body?: EpisodeGenerateBody,
): Promise<EpisodesCommandResult> {
  return http.post<EpisodesCommandResult>(`${episodesBase(projectId)}generate/`, body ?? {})
}

export async function confirmEpisodePlan(projectId: string): Promise<EpisodesCommandResult> {
  return http.post<EpisodesCommandResult>(`${episodesBase(projectId)}confirm/`, {})
}

export async function reviseEpisodePlan(
  projectId: string,
  body: EpisodeReviseBody,
): Promise<EpisodesCommandResult> {
  return http.post<EpisodesCommandResult>(`${episodesBase(projectId)}revise/`, body)
}
