import { formatDateTime } from '@/utils/date'
import { normalizeWorkStatus } from '@/utils/workStatus'
import { CREATION_STATUS_TEXT } from '../constants/businessEnums'

export function normalizeMembership(raw) {
  if (!raw) return null
  const plan = raw.plan || {}
  const wallet = raw.wallet || {}
  return {
    ...raw,
    plan_name: plan.name || raw.plan_name,
    end_at: raw.end_at || null,
    remaining_days:
      typeof raw.remaining_days === 'number' && Number.isFinite(raw.remaining_days)
        ? Math.max(0, raw.remaining_days)
        : undefined,
    wallet: {
      currency_name: wallet.currency_name,
      balance: wallet.balance,
    },
    is_active: Boolean(raw.is_active && !raw.is_expired),
    grant_coins: plan.grant_coins ?? raw.grant_coins,
  }
}

export function normalizeOrder(raw) {
  if (!raw) return null
  return {
    ...raw,
    plan_name: raw.membership_plan?.name || raw.plan_name,
  }
}

export function normalizeWorkItem(work) {
  if (!work) return null
  const status = normalizeWorkStatus(work.status, work)
  const createdAt = work.created_at ? formatDateTime(work.created_at) : ''
  return {
    ...work,
    project_id: work.project_id,
    raw_status: work.status,
    title: work.title,
    theme: work.theme,
    episodes: work.episode_count,
    status,
    status_text: work.status_text,
    progress_percent: work.progress_percent ?? 0,
    completion_rate: work.completion_rate ?? work.progress_percent ?? 0,
    delivery_status: work.delivery_status || 'pending',
    target_platform: work.target_platform || '',
    pipeline_mode: work.pipeline_mode,
    score: work.overall_score,
    fusionStatus: work.status,
    grade: work.grade,
    createdAt,
    idea: (work.core_idea || '').trim(),
    format: work.format_variant,
  }
}

export function normalizeWorkDetail(work) {
  if (!work) return null
  const base = normalizeWorkItem(work)
  const fusionSnapshot = work.fusion_snapshot || {}
  const scoreReport = fusionSnapshot.score_report || null
  return {
    ...work,
    ...base,
    resultHtml: work.result_html || '',
    progressHtml: work.progress_html || '',
    fusionSnapshot,
    gateSummary: fusionSnapshot.gate_summary || null,
    scoreReport: scoreReport || (work.overall_score != null
      ? {
          overallScore: work.overall_score,
          grade: work.grade,
        }
      : null),
    reviewReport: fusionSnapshot.review_report || null,
    marketingKit: fusionSnapshot.marketing_kit || null,
    polishLog: fusionSnapshot.polish_log || null,
    projectBrief: fusionSnapshot.project_brief || null,
    structureWarnings: fusionSnapshot.structure_warnings || [],
  }
}

export function normalizeCreationSubmitResult(raw) {
  if (!raw) return raw
  return raw
}

export function normalizeCreationProgress(raw) {
  if (!raw) return raw
  return {
    ...raw,
    progress: Number(raw.progress_percent ?? 0),
    progress_percent: Number(raw.progress_percent ?? 0),
    status_text: raw.status_text || CREATION_STATUS_TEXT[raw.status],
  }
}
