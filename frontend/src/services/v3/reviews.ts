import { http } from '@/services/http'
import type {
  ScriptReviewCompare,
  ScriptReviewDetail,
  ScriptReviewList,
  ScriptReviewRun,
  ScriptReviewRunKind,
} from '@/types/v3/domain'

const BASE = '/api/v3/reviews/'

export type CreateScriptReviewBody = {
  script_text: string
  title?: string
  project_id?: string | null
}

export type ListScriptReviewsParams = {
  project_id?: string
}

export async function listScriptReviews(
  params?: ListScriptReviewsParams,
): Promise<ScriptReviewList> {
  const query: Record<string, string> = {}
  if (params?.project_id) query.project_id = params.project_id
  const options = Object.keys(query).length > 0 ? { params: query } : undefined
  return http.get<ScriptReviewList>(BASE, options)
}

export async function createScriptReview(
  body: CreateScriptReviewBody,
): Promise<ScriptReviewDetail> {
  return http.post<ScriptReviewDetail>(BASE, body)
}

export async function createScriptReviewUpload(form: FormData): Promise<ScriptReviewDetail> {
  return http.post<ScriptReviewDetail>(BASE, form)
}

export async function getScriptReview(reviewId: string): Promise<ScriptReviewDetail> {
  return http.get<ScriptReviewDetail>(`${BASE}${reviewId}/`)
}

export async function scoreScriptReview(
  reviewId: string,
): Promise<{ run: ScriptReviewRun }> {
  return http.post<{ run: ScriptReviewRun }>(`${BASE}${reviewId}/score/`, {})
}

export async function checkScriptReviewCompliance(
  reviewId: string,
): Promise<{ run: ScriptReviewRun }> {
  return http.post<{ run: ScriptReviewRun }>(`${BASE}${reviewId}/compliance/`, {})
}

export async function listScriptReviewRuns(
  reviewId: string,
  params?: { kind?: ScriptReviewRunKind },
): Promise<{ items: ScriptReviewRun[] }> {
  const query: Record<string, string> = {}
  if (params?.kind) query.kind = params.kind
  const options = Object.keys(query).length > 0 ? { params: query } : undefined
  return http.get<{ items: ScriptReviewRun[] }>(`${BASE}${reviewId}/runs/`, options)
}

export async function getScriptReviewRun(
  reviewId: string,
  runId: string,
): Promise<ScriptReviewRun> {
  return http.get<ScriptReviewRun>(`${BASE}${reviewId}/runs/${runId}/`)
}

export async function compareScriptReviewRuns(
  reviewId: string,
  a: string,
  b: string,
): Promise<ScriptReviewCompare> {
  return http.get<ScriptReviewCompare>(`${BASE}${reviewId}/compare/`, {
    params: { a, b },
  })
}
