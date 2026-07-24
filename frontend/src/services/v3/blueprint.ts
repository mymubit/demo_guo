import { http } from '@/services/http'
import type { BlueprintState, CommandRunSummary } from '@/types/v3/domain'

function blueprintBase(projectId: string): string {
  return `/api/v3/projects/${projectId}/blueprint/`
}

export type BlueprintCommandResult = {
  command_run: CommandRunSummary
}

export async function getBlueprintState(projectId: string): Promise<BlueprintState> {
  return http.get<BlueprintState>(blueprintBase(projectId))
}

export async function generateBlueprint(projectId: string): Promise<BlueprintCommandResult> {
  return http.post<BlueprintCommandResult>(`${blueprintBase(projectId)}generate/`)
}

export async function confirmBlueprint(projectId: string): Promise<BlueprintCommandResult> {
  return http.post<BlueprintCommandResult>(`${blueprintBase(projectId)}confirm/`, {})
}
