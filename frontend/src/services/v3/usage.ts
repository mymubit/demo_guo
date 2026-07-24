import { http } from '@/services/http'
import type { UsageSummary, UsageSummaryQuery } from '@/types/v3/domain'

const SUMMARY_PATH = '/api/v3/usage/summary/'

function cleanParams(params?: UsageSummaryQuery): Record<string, unknown> | undefined {
  if (!params) return undefined
  const next: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    next[key] = value
  }
  return Object.keys(next).length > 0 ? next : undefined
}

export async function getUsageSummary(query: UsageSummaryQuery = {}): Promise<UsageSummary> {
  const params = cleanParams(query)
  return http.get<UsageSummary>(SUMMARY_PATH, params ? { params } : undefined)
}
