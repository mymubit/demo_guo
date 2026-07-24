import { http } from '@/services/http'
import type {
  CommandRunSummary,
  ScriptDraft,
  ScriptDraftPayload,
  ScriptEpisodeState,
  ScriptsState,
} from '@/types/v3/domain'

function scriptsBase(projectId: string): string {
  return `/api/v3/projects/${projectId}/scripts/`
}

export type ScriptsCommandResult = {
  command_run: CommandRunSummary
}

export type ScriptGenerateBody = {
  start: number
  end: number
  writing_requests?: Record<string, unknown>
}

export type ScriptConfirmBody = {
  use_drafts?: boolean
}

export async function getScriptsState(projectId: string): Promise<ScriptsState> {
  return http.get<ScriptsState>(scriptsBase(projectId))
}

export async function getScriptEpisode(
  projectId: string,
  episodeNumber: number,
): Promise<ScriptEpisodeState> {
  return http.get<ScriptEpisodeState>(`${scriptsBase(projectId)}${episodeNumber}/`)
}

export async function putScriptDraft(
  projectId: string,
  episodeNumber: number,
  payload: ScriptDraftPayload | Record<string, unknown>,
): Promise<ScriptDraft> {
  return http.put<ScriptDraft>(`${scriptsBase(projectId)}${episodeNumber}/draft/`, { payload })
}

export async function generateScriptBatch(
  projectId: string,
  body: ScriptGenerateBody,
): Promise<ScriptsCommandResult> {
  return http.post<ScriptsCommandResult>(`${scriptsBase(projectId)}generate/`, body)
}

export async function confirmScriptCandidate(
  projectId: string,
  body?: ScriptConfirmBody,
): Promise<ScriptsCommandResult> {
  return http.post<ScriptsCommandResult>(`${scriptsBase(projectId)}confirm/`, body ?? {})
}
