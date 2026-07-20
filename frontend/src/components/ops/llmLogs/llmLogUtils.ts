import type { LlmCallLogItem } from '@/services/admin'
import { formatRoleLabel, ROLE_FILTER_OPTIONS } from '@/utils/roleLabels'

export const PURPOSE_LABEL: Record<string, string> = {
  artifact_generation: '角色产物',
  quality_scoring: '质量评分',
  compliance_check: '合规检查',
  connectivity_test: '连通测试',
}

export const JOB_STATUS_LABEL: Record<string, string> = {
  pending: '等待中',
  queued: '排队中',
  running: '运行中',
  completed: '已落库',
  failed: '任务失败',
  disabled: '已禁用',
}

export type JobOutcome = {
  tone: 'ok' | 'warn' | 'bad' | 'neutral'
  label: string
  shortLabel: string
}

export type DetailTab = 'meta' | 'injection' | 'system' | 'user' | 'response'

export type JobChain = {
  key: string
  jobId: string | null
  projectId: string | null
  projectTitle: string
  items: LlmCallLogItem[]
  latestAt: string | null
  hasError: boolean
  errorCount: number
  totalLatency: number
  totalTokens: number
}

export type ProjectGroup = {
  key: string
  projectId: string | null
  projectTitle: string
  jobs: JobChain[]
  latestAt: string | null
  hasError: boolean
  errorCount: number
  totalCalls: number
}

export function classifyJobOutcome(item: LlmCallLogItem): JobOutcome | null {
  if (!item.job_id) return null
  const err = item.job_error_message || ''
  const errLower = err.toLowerCase()

  if (item.job_status === 'completed') {
    return { tone: 'ok', label: '工作台已落库', shortLabel: '已落库' }
  }
  if (item.job_status === 'running' || item.job_status === 'queued') {
    return { tone: 'warn', label: '工作台任务进行中', shortLabel: '进行中' }
  }
  if (item.job_status !== 'failed' && item.job_status !== 'disabled') {
    if (!item.job_status) return null
    const label = JOB_STATUS_LABEL[item.job_status] ?? item.job_status
    return { tone: 'neutral', label: `工作台：${label}`, shortLabel: label }
  }

  if (/不是合法\s*json|jsondecodeerror|expecting property name|unexpected token/i.test(err)) {
    return { tone: 'warn', label: 'JSON 解析失败', shortLabel: 'JSON 失败' }
  }
  if (/schema|不合规|required property|校验失败|is not of type/i.test(err)) {
    return { tone: 'warn', label: 'Schema 未通过', shortLabel: 'Schema' }
  }
  if (/timed?\s*out|timeout|read timed out/i.test(errLower)) {
    return { tone: 'bad', label: '模型读超时', shortLabel: '超时' }
  }
  if (/response_format|json_object|invalidparameter/i.test(errLower)) {
    return { tone: 'bad', label: '模型不支持 JSON 参数', shortLabel: '参数不支持' }
  }
  if (/卡住|手动结束|stale/i.test(err)) {
    return { tone: 'bad', label: '任务被结束或卡住', shortLabel: '已结束' }
  }
  if (item.status === 'success') {
    return { tone: 'warn', label: '调用成功但未落库', shortLabel: '未落库' }
  }
  return { tone: 'bad', label: '工作台任务失败', shortLabel: '任务失败' }
}

export const OUTCOME_TONE_CLASS: Record<JobOutcome['tone'], string> = {
  ok: 'text-emerald-700',
  warn: 'text-amber-800',
  bad: 'text-red-600',
  neutral: 'text-ink-muted',
}

export function formatClock(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return iso
  }
}

export function formatLatency(ms: number): string {
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

export function shortId(id: string | null | undefined, len = 8): string {
  if (!id) return '—'
  return id.length <= len ? id : `${id.slice(0, len)}…`
}

export function projectTitleOf(item: LlmCallLogItem): string {
  if (item.project_title?.trim()) return item.project_title.trim()
  if (item.project_id) return `项目 ${shortId(item.project_id)}`
  return '无项目（连通测试）'
}

export function groupByJob(items: LlmCallLogItem[]): JobChain[] {
  const map = new Map<string, LlmCallLogItem[]>()
  for (const item of items) {
    const key = item.job_id || `orphan:${item.id}`
    const list = map.get(key) ?? []
    list.push(item)
    map.set(key, list)
  }
  return [...map.entries()]
    .map(([key, groupItems]) => {
      const sorted = [...groupItems].sort((a, b) => {
        if (a.seq_in_job !== b.seq_in_job) return a.seq_in_job - b.seq_in_job
        const ta = a.created_at ? Date.parse(a.created_at) : 0
        const tb = b.created_at ? Date.parse(b.created_at) : 0
        return ta - tb
      })
      const head = sorted[0]
      const errorCount = sorted.filter((i) => i.status !== 'success').length
      return {
        key,
        jobId: sorted.find((i) => i.job_id)?.job_id ?? null,
        projectId: sorted.find((i) => i.project_id)?.project_id ?? null,
        projectTitle: head ? projectTitleOf(head) : '—',
        items: sorted,
        latestAt: sorted[sorted.length - 1]?.created_at ?? null,
        hasError: errorCount > 0,
        errorCount,
        totalLatency: sorted.reduce((sum, i) => sum + (i.latency_ms || 0), 0),
        totalTokens: sorted.reduce((sum, i) => sum + (i.total_tokens || 0), 0),
      }
    })
    .sort((a, b) => {
      const ta = a.latestAt ? Date.parse(a.latestAt) : 0
      const tb = b.latestAt ? Date.parse(b.latestAt) : 0
      return tb - ta
    })
}

export function groupByProject(items: LlmCallLogItem[]): ProjectGroup[] {
  const jobs = groupByJob(items)
  const map = new Map<string, JobChain[]>()
  for (const job of jobs) {
    const key = job.projectId || 'no-project'
    const list = map.get(key) ?? []
    list.push(job)
    map.set(key, list)
  }
  const groups = [...map.entries()].map(([key, projectJobs]) => {
    const sortedJobs = [...projectJobs].sort((a, b) => {
      const ta = a.latestAt ? Date.parse(a.latestAt) : 0
      const tb = b.latestAt ? Date.parse(b.latestAt) : 0
      return tb - ta
    })
    const head = sortedJobs[0]
    const errorCount = sortedJobs.reduce((sum, j) => sum + j.errorCount, 0)
    return {
      key,
      projectId: head?.projectId ?? null,
      projectTitle: head?.projectTitle ?? '无项目（连通测试）',
      jobs: sortedJobs,
      latestAt: head?.latestAt ?? null,
      hasError: errorCount > 0,
      errorCount,
      totalCalls: sortedJobs.reduce((sum, j) => sum + j.items.length, 0),
    }
  })

  const withProject = groups
    .filter((g) => g.projectId)
    .sort((a, b) => {
      const ta = a.latestAt ? Date.parse(a.latestAt) : 0
      const tb = b.latestAt ? Date.parse(b.latestAt) : 0
      return tb - ta
    })
  const orphans = groups.filter((g) => !g.projectId)
  return [...withProject, ...orphans]
}

/** 客户端：工作台结果筛选 */
export function matchWorkbenchFilter(item: LlmCallLogItem, value: string): boolean {
  if (!value) return true
  const outcome = classifyJobOutcome(item)
  if (value === 'persisted') return outcome?.tone === 'ok'
  if (value === 'bench_warn') return outcome?.tone === 'warn'
  if (value === 'bench_fail') return outcome?.tone === 'bad' || item.job_status === 'failed'
  if (value === 'no_job') return !item.job_id
  return true
}

export { formatRoleLabel, ROLE_FILTER_OPTIONS }
