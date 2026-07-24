import { http } from '@/services/http'
import type { ArtifactVersion, CommandRunSummary, TopicState } from '@/types/v3/domain'

function topicBase(projectId: string): string {
  return `/api/v3/projects/${projectId}/topic/`
}

export type TopicCommandResult = {
  command_run: CommandRunSummary
}

export async function getTopicState(projectId: string): Promise<TopicState> {
  return http.get<TopicState>(topicBase(projectId))
}

export async function saveTopicDraft(
  projectId: string,
  payload: Record<string, unknown>,
): Promise<ArtifactVersion> {
  return http.put<ArtifactVersion>(`${topicBase(projectId)}draft/`, { payload })
}

export async function generateTopicBrief(projectId: string): Promise<TopicCommandResult> {
  return http.post<TopicCommandResult>(`${topicBase(projectId)}generate/`)
}

export async function confirmTopicBrief(
  projectId: string,
  options?: { use_draft?: boolean },
): Promise<TopicCommandResult> {
  const body = options?.use_draft ? { use_draft: true } : {}
  return http.post<TopicCommandResult>(`${topicBase(projectId)}confirm/`, body)
}
