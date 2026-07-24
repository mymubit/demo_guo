import { http } from '@/services/http'
import type { LogCall, LogRun, LogRunList } from '@/types/v3/domain'

const RUNS_PATH = '/api/v3/logs/runs/'
const CALLS_PATH = '/api/v3/logs/calls/'

export type ListLogRunsParams = {
  project_id?: string
  status?: string
  command_type?: string
  created_after?: string
  created_before?: string
  limit?: number
  offset?: number
}

function cleanParams(params?: ListLogRunsParams): Record<string, unknown> | undefined {
  if (!params) return undefined
  const next: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    next[key] = value
  }
  return Object.keys(next).length > 0 ? next : undefined
}

export async function listLogRuns(params?: ListLogRunsParams): Promise<LogRunList> {
  const query = cleanParams(params)
  return http.get<LogRunList>(RUNS_PATH, query ? { params: query } : undefined)
}

export async function getLogRun(runId: string): Promise<LogRun> {
  return http.get<LogRun>(`${RUNS_PATH}${runId}/`)
}

export async function getLogCall(callId: string): Promise<LogCall> {
  return http.get<LogCall>(`${CALLS_PATH}${callId}/`)
}
