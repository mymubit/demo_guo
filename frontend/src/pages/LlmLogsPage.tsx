import { useEffect, useMemo, useRef, useState, type MutableRefObject } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowRight, Filter, RefreshCw, X } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { PageShell } from '@/components/layout/PageShell'
import { adminApi, type LlmCallLogItem, type LlmCallLogDetail } from '@/services/admin'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { cn } from '@/utils/cn'
import { formatRelativeTime } from '@/utils/recentProjects'
import { formatRoleLabel, ROLE_FILTER_OPTIONS } from '@/utils/roleLabels'

const PURPOSE_LABEL: Record<string, string> = {
  artifact_generation: '角色产物',
  quality_scoring: '质量评分',
  compliance_check: '合规检查',
  connectivity_test: '连通测试',
}

const JOB_STATUS_LABEL: Record<string, string> = {
  pending: '等待中',
  queued: '排队中',
  running: '运行中',
  completed: '已落库',
  failed: '任务失败',
  disabled: '已禁用',
}

type JobOutcome = {
  tone: 'ok' | 'warn' | 'bad' | 'neutral'
  /** 短标签 */
  label: string
}

/** 把「模型调用」和「工作台落库」拆开，避免调用成功也被画成一体式大红错。 */
function classifyJobOutcome(item: LlmCallLogItem): JobOutcome | null {
  if (!item.job_id) return null
  const err = item.job_error_message || ''
  const errLower = err.toLowerCase()

  if (item.job_status === 'completed') {
    return { tone: 'ok', label: '工作台：已落库' }
  }
  if (item.job_status === 'running' || item.job_status === 'queued') {
    return { tone: 'warn', label: '工作台：任务仍在进行（若已很久请回工作台结束）' }
  }
  if (item.job_status !== 'failed' && item.job_status !== 'disabled') {
    if (!item.job_status) return null
    return {
      tone: 'neutral',
      label: `工作台：${JOB_STATUS_LABEL[item.job_status] ?? item.job_status}`,
    }
  }

  if (/不是合法\s*json|jsondecodeerror|expecting property name|unexpected token/i.test(err)) {
    return {
      tone: 'warn',
      label: '工作台：JSON 解析失败（模型已有回复，内容不合法）',
    }
  }
  if (/schema|不合规|required property|校验失败|is not of type/i.test(err)) {
    return {
      tone: 'warn',
      label: '工作台：Schema 未过（JSON 往往已解析成功，只是字段不合规）',
    }
  }
  if (/timed?\s*out|timeout|read timed out/i.test(errLower)) {
    return { tone: 'bad', label: '工作台：模型读超时' }
  }
  if (/response_format|json_object|invalidparameter/i.test(errLower)) {
    return { tone: 'bad', label: '工作台：模型不支持当前 JSON 参数' }
  }
  if (/卡住|手动结束|stale/i.test(err)) {
    return { tone: 'bad', label: '工作台：任务被结束或判定卡住' }
  }
  if (item.status === 'success') {
    return {
      tone: 'warn',
      label: '工作台：落库失败（模型调用本身已成功）',
    }
  }
  return { tone: 'bad', label: '工作台：任务失败' }
}

const OUTCOME_TONE_CLASS: Record<JobOutcome['tone'], string> = {
  ok: 'text-emerald-700',
  warn: 'text-amber-800',
  bad: 'text-red-600',
  neutral: 'text-ink-muted',
}

type DetailTab = 'meta' | 'system' | 'user' | 'response'

function formatClock(iso: string | null | undefined): string {
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

function formatLatency(ms: number): string {
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

function shortId(id: string | null | undefined, len = 8): string {
  if (!id) return '—'
  return id.length <= len ? id : `${id.slice(0, len)}…`
}

function projectTitleOf(item: LlmCallLogItem): string {
  if (item.project_title?.trim()) return item.project_title.trim()
  if (item.project_id) return `项目 ${shortId(item.project_id)}`
  return '无项目（连通测试）'
}

type JobChain = {
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

type ProjectGroup = {
  key: string
  projectId: string | null
  projectTitle: string
  jobs: JobChain[]
  latestAt: string | null
  hasError: boolean
  errorCount: number
  totalCalls: number
}

function groupByJob(items: LlmCallLogItem[]): JobChain[] {
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

function groupByProject(items: LlmCallLogItem[]): ProjectGroup[] {
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

/** logs / chains 同页；mode 仅保留路由兼容。 */
export function LlmLogsPage(_props?: { mode?: 'logs' | 'chains' }) {
  const [params, setParams] = useSearchParams()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [activeProjectKey, setActiveProjectKey] = useState<string | null>(null)
  const [highlightJobKey, setHighlightJobKey] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(() =>
    Boolean(params.get('role') || params.get('status') || params.get('job_id')),
  )
  const [showMoreFilters, setShowMoreFilters] = useState(() => Boolean(params.get('job_id')))
  const [detailTab, setDetailTab] = useState<DetailTab>('meta')
  const jobRefs = useRef<Record<string, HTMLElement | null>>({})
  const deepLinkApplied = useRef(false)

  const filters = useMemo(
    () => ({
      project_id: params.get('project_id') || undefined,
      job_id: params.get('job_id') || undefined,
      role: params.get('role') || undefined,
      status: params.get('status') || undefined,
    }),
    [params],
  )

  const listQuery = useQuery({
    queryKey: ['admin-llm-logs', filters.job_id, filters.role, filters.status],
    queryFn: () =>
      adminApi.getLlmLogs({
        job_id: filters.job_id,
        role: filters.role,
        status: filters.status,
        limit: 200,
      }),
  })

  const detailQuery = useQuery({
    queryKey: ['llm-log-detail', selectedId],
    queryFn: () => dramaApi.getLlmLogDetail(selectedId!),
    enabled: Boolean(selectedId),
  })

  const items = listQuery.data?.items ?? []
  const projectGroups = useMemo(() => groupByProject(items), [items])

  const activeProject = useMemo(() => {
    if (activeProjectKey) {
      return projectGroups.find((p) => p.key === activeProjectKey) ?? null
    }
    return projectGroups[0] ?? null
  }, [activeProjectKey, projectGroups])

  useEffect(() => {
    if (projectGroups.length === 0) {
      setActiveProjectKey(null)
      return
    }
    if (activeProjectKey && projectGroups.some((p) => p.key === activeProjectKey)) return

    const fromQuery = filters.project_id
      ? projectGroups.find((p) => p.projectId === filters.project_id)
      : null
    const fromJob = filters.job_id
      ? projectGroups.find((p) => p.jobs.some((j) => j.jobId === filters.job_id))
      : null
    setActiveProjectKey((fromQuery ?? fromJob ?? projectGroups[0]).key)
  }, [projectGroups, activeProjectKey, filters.project_id, filters.job_id])

  useEffect(() => {
    if (deepLinkApplied.current || !filters.job_id || !activeProject) return
    const job = activeProject.jobs.find((j) => j.jobId === filters.job_id)
    if (!job) return
    deepLinkApplied.current = true
    setHighlightJobKey(job.key)
    setSelectedId(job.items[0]?.id ?? null)
    requestAnimationFrame(() => {
      jobRefs.current[job.key]?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }, [filters.job_id, activeProject])

  useEffect(() => {
    setDetailTab('meta')
  }, [selectedId])

  function patchFilter(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  function selectProject(group: ProjectGroup) {
    setActiveProjectKey(group.key)
    setSelectedId(null)
    setHighlightJobKey(null)
    deepLinkApplied.current = true
    const next = new URLSearchParams(params)
    next.delete('job_id')
    if (group.projectId) next.set('project_id', group.projectId)
    else next.delete('project_id')
    setParams(next, { replace: true })
  }

  function openCall(id: string) {
    setSelectedId(id)
  }

  function closeDrawer() {
    setSelectedId(null)
  }

  return (
    <PageShell
      title="LLM 调用"
      description="以项目查看角色生成与质检的模型调用；点一行打开详情。"
      actions={
        <>
          <Button
            size="sm"
            variant="secondary"
            iconLeft={<Filter className="h-3.5 w-3.5" />}
            onClick={() => setShowFilters((v) => !v)}
          >
            筛选
          </Button>
          <Button
            size="sm"
            variant="secondary"
            iconLeft={<RefreshCw className="h-3.5 w-3.5" />}
            onClick={() => {
              void listQuery.refetch()
              if (selectedId) void detailQuery.refetch()
            }}
          >
            刷新
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-5">
        {showFilters ? (
          <section className="sf-panel grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3">
            <label className="block text-sm">
              <span className="sf-label">角色</span>
              <select
                className="sf-control mt-1"
                value={filters.role ?? ''}
                onChange={(e) => patchFilter('role', e.target.value)}
              >
                <option value="">全部角色</option>
                {ROLE_FILTER_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              <span className="sf-label">状态</span>
              <select
                className="sf-control mt-1"
                value={filters.status ?? ''}
                onChange={(e) => patchFilter('status', e.target.value)}
              >
                <option value="">全部</option>
                <option value="success">成功</option>
                <option value="error">失败</option>
              </select>
            </label>
            <div className="flex items-end">
              <button
                type="button"
                className="text-xs text-action hover:underline"
                onClick={() => setShowMoreFilters((v) => !v)}
              >
                {showMoreFilters ? '收起更多' : '更多筛选'}
              </button>
            </div>
            {showMoreFilters ? (
              <label className="block text-sm sm:col-span-2 lg:col-span-3">
                <span className="sf-label">任务 ID</span>
                <input
                  className="sf-control mt-1 max-w-md"
                  value={filters.job_id ?? ''}
                  onChange={(e) => patchFilter('job_id', e.target.value.trim())}
                  placeholder="可选，精确匹配 generation job"
                />
              </label>
            ) : null}
          </section>
        ) : null}

        {listQuery.isLoading ? <LoadingBlock label="加载中…" /> : null}
        {listQuery.isError ? <ErrorBanner message={formatApiError(listQuery.error)} /> : null}

        {!listQuery.isLoading && !listQuery.isError ? (
          <div className="grid min-h-[32rem] gap-5 xl:grid-cols-[17rem_minmax(0,1fr)]">
            <ProjectSidebar
              groups={projectGroups}
              activeKey={activeProject?.key ?? null}
              onSelect={selectProject}
            />

            <main className="min-w-0">
              {activeProject ? (
                <ProjectActivity
                  group={activeProject}
                  highlightJobKey={highlightJobKey}
                  selectedId={selectedId}
                  jobRefs={jobRefs}
                  onOpenCall={openCall}
                  initialRole={highlightJobKey ? undefined : filters.role}
                />
              ) : (
                <div className="sf-panel">
                  <EmptyState
                    title="暂无调用记录"
                    description="跑一次生成或模型连通测试后，会按项目出现在这里。"
                  />
                </div>
              )}
            </main>
          </div>
        ) : null}
      </div>

      {selectedId ? (
        <DetailDrawer
          detail={detailQuery.data}
          loading={detailQuery.isLoading}
          error={detailQuery.error}
          tab={detailTab}
          onTabChange={setDetailTab}
          onClose={closeDrawer}
        />
      ) : null}
    </PageShell>
  )
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={cn('inline-block h-2 w-2 shrink-0 rounded-full', ok ? 'bg-emerald-500' : 'bg-red-500')}
      title={ok ? '成功' : '失败'}
    />
  )
}

function ProjectSidebar({
  groups,
  activeKey,
  onSelect,
}: {
  groups: ProjectGroup[]
  activeKey: string | null
  onSelect: (group: ProjectGroup) => void
}) {
  return (
    <aside className="sf-panel flex max-h-[calc(100dvh-10rem)] min-h-[28rem] flex-col overflow-hidden xl:sticky xl:top-6">
      <div className="border-b border-border px-4 py-3 text-sm font-semibold text-ink">
        项目
        <span className="ml-1.5 font-normal text-ink-faint">{groups.length}</span>
      </div>
      {groups.length === 0 ? (
        <p className="px-4 py-12 text-center text-sm text-ink-muted">暂无</p>
      ) : (
        <ul className="flex-1 overflow-y-auto">
          {groups.map((group) => {
            const active = group.key === activeKey
            return (
              <li key={group.key}>
                <button
                  type="button"
                  onClick={() => onSelect(group)}
                  className={cn(
                    'w-full border-b border-border/60 px-4 py-3.5 text-left transition',
                    active ? 'bg-action/5' : 'hover:bg-canvas-muted/60',
                  )}
                >
                  <div className="flex items-start gap-2">
                    <span className="mt-1.5 shrink-0">
                      <StatusDot ok={!group.hasError} />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium text-ink" title={group.projectTitle}>
                        {group.projectTitle}
                      </span>
                      <span
                        className={cn(
                          'mt-1 block text-[11px]',
                          active ? 'text-ink-faint' : 'text-ink-muted',
                        )}
                      >
                        {group.totalCalls} 次调用 · {formatRelativeTime(group.latestAt)}
                        {group.errorCount > 0 ? ` · ${group.errorCount} 失败` : ''}
                      </span>
                    </span>
                  </div>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </aside>
  )
}

function ProjectActivity({
  group,
  highlightJobKey,
  selectedId,
  jobRefs,
  onOpenCall,
  initialRole,
}: {
  group: ProjectGroup
  highlightJobKey: string | null
  selectedId: string | null
  jobRefs: MutableRefObject<Record<string, HTMLElement | null>>
  onOpenCall: (id: string) => void
  initialRole?: string
}) {
  const roleTabs = useMemo(() => buildRoleTabs(group), [group])
  const roleKeySig = roleTabs.map((t) => t.role).join('|')
  const [activeRole, setActiveRole] = useState<string>('all')

  useEffect(() => {
    setActiveRole((prev) => {
      if (initialRole && roleTabs.some((t) => t.role === initialRole)) return initialRole
      if (prev !== 'all' && roleTabs.some((t) => t.role === prev)) return prev
      return 'all'
    })
    // roleKeySig 代表当前项目下角色集合变化
    // eslint-disable-next-line react-hooks/exhaustive-deps -- 仅在项目或角色集合 / 深链角色变化时归位
  }, [group.key, roleKeySig, initialRole])

  const roleCalls = useMemo(() => {
    if (activeRole === 'all') return []
    const calls: LlmCallLogItem[] = []
    for (const job of group.jobs) {
      for (const item of job.items) {
        if (item.role === activeRole) calls.push(item)
      }
    }
    return calls.sort((a, b) => {
      const ta = a.created_at ? Date.parse(a.created_at) : 0
      const tb = b.created_at ? Date.parse(b.created_at) : 0
      return tb - ta
    })
  }, [activeRole, group.jobs])

  const activeTab = roleTabs.find((t) => t.role === activeRole) ?? roleTabs[0]

  return (
    <div className="space-y-4">
      <section className="sf-panel overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border bg-canvas-muted/40 px-5 py-4">
          <div className="min-w-0">
            <div className="text-xs font-medium tracking-wide text-ink-muted">当前项目</div>
            <div className="mt-1 truncate text-lg font-semibold text-ink">{group.projectTitle}</div>
            <div className="mt-1 text-xs text-ink-faint">
              {group.jobs.length} 次任务 · {group.totalCalls} 次调用
              {group.errorCount > 0 ? ` · ${group.errorCount} 失败` : ' · 全部成功'}
              {group.latestAt ? ` · 最近 ${formatRelativeTime(group.latestAt)}` : ''}
            </div>
          </div>
          {group.projectId ? (
            <Link to={`/projects/${group.projectId}/workbench`}>
              <Button
                size="sm"
                variant="action"
                iconLeft={<ArrowRight className="h-3.5 w-3.5" />}
              >
                打开工作台
              </Button>
            </Link>
          ) : null}
        </div>

        {roleTabs.length > 1 ? (
          <div className="flex gap-1 overflow-x-auto border-t border-border bg-canvas-muted/60 px-3 py-2">
            {roleTabs.map((tab) => {
              const active = tab.role === activeRole
              return (
                <button
                  key={tab.role}
                  type="button"
                  onClick={() => setActiveRole(tab.role)}
                  className={cn(
                    'shrink-0 rounded-md px-3 py-1.5 text-xs font-medium transition',
                    active
                      ? 'bg-action text-white'
                      : 'text-ink-muted hover:bg-canvas-muted hover:text-ink',
                  )}
                >
                  {tab.label}
                  <span className={cn('ml-1.5 tabular-nums', active ? 'text-white/70' : 'text-ink-faint')}>
                    {tab.count}
                  </span>
                  {tab.errorCount > 0 ? (
                    <span className={cn('ml-1', active ? 'text-red-200' : 'text-red-600')}>·</span>
                  ) : null}
                </button>
              )
            })}
          </div>
        ) : null}
      </section>

      {group.jobs.length === 0 ? (
        <div className="sf-panel">
          <EmptyState title="该项目暂无调用" description="在工作台跑主链或质检后会出现任务分段。" />
        </div>
      ) : activeRole === 'all' ? (
        <JobSections
          jobs={group.jobs}
          highlightJobKey={highlightJobKey}
          selectedId={selectedId}
          jobRefs={jobRefs}
          onOpenCall={onOpenCall}
          showRoleInRow
        />
      ) : (
        <RoleCallList
          roleLabel={activeTab?.label ?? formatRoleLabel(activeRole)}
          calls={roleCalls}
          selectedId={selectedId}
          onOpenCall={onOpenCall}
        />
      )}
    </div>
  )
}

type RoleTab = {
  role: string
  label: string
  count: number
  errorCount: number
  latestAt: string | null
}

function buildRoleTabs(group: ProjectGroup): RoleTab[] {
  const map = new Map<string, RoleTab>()
  for (const job of group.jobs) {
    for (const item of job.items) {
      const role = item.role || 'unknown'
      const existing = map.get(role)
      const ok = item.status === 'success'
      if (!existing) {
        map.set(role, {
          role,
          label: formatRoleLabel(item.role, item.role_label),
          count: 1,
          errorCount: ok ? 0 : 1,
          latestAt: item.created_at,
        })
      } else {
        existing.count += 1
        if (!ok) existing.errorCount += 1
        const ta = item.created_at ? Date.parse(item.created_at) : 0
        const tb = existing.latestAt ? Date.parse(existing.latestAt) : 0
        if (ta > tb) existing.latestAt = item.created_at
      }
    }
  }

  const orderIndex = new Map(ROLE_FILTER_OPTIONS.map((o, i) => [o.value, i]))
  const roles = [...map.values()].sort((a, b) => {
    const ia = orderIndex.get(a.role) ?? 999
    const ib = orderIndex.get(b.role) ?? 999
    if (ia !== ib) return ia - ib
    const ta = a.latestAt ? Date.parse(a.latestAt) : 0
    const tb = b.latestAt ? Date.parse(b.latestAt) : 0
    return tb - ta
  })

  const totalErrors = group.errorCount
  return [
    {
      role: 'all',
      label: '全部',
      count: group.totalCalls,
      errorCount: totalErrors,
      latestAt: group.latestAt,
    },
    ...roles,
  ]
}

function JobSections({
  jobs,
  highlightJobKey,
  selectedId,
  jobRefs,
  onOpenCall,
  showRoleInRow,
}: {
  jobs: JobChain[]
  highlightJobKey: string | null
  selectedId: string | null
  jobRefs: MutableRefObject<Record<string, HTMLElement | null>>
  onOpenCall: (id: string) => void
  showRoleInRow: boolean
}) {
  return (
    <div className="space-y-4">
      {jobs.map((job, index) => {
        const highlighted = job.key === highlightJobKey
        return (
          <section
            key={job.key}
            ref={(el) => {
              jobRefs.current[job.key] = el
            }}
            className={cn(
              'overflow-hidden rounded-xl border bg-surface shadow-panel',
              highlighted ? 'border-action ring-2 ring-action/20' : 'border-border',
            )}
          >
            <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border px-5 py-3">
              <div className="min-w-0">
                <h3 className="text-sm font-semibold text-ink">
                  {job.jobId ? `生成任务 ${index + 1}` : '单次探测'}
                  <span className="ml-2 font-normal text-ink-muted">
                    · {formatRelativeTime(job.latestAt)}
                  </span>
                </h3>
                <p className="mt-0.5 text-[11px] text-ink-faint">
                  {job.items.length} 步 · {formatLatency(job.totalLatency)}
                  {job.totalTokens > 0 ? ` · ${job.totalTokens} tokens` : ''}
                  {job.jobId ? ` · ${shortId(job.jobId, 10)}` : ''}
                </p>
              </div>
              {job.hasError ? (
                <span className="text-xs text-red-600">{job.errorCount} 步失败</span>
              ) : (
                <span className="text-xs text-emerald-700">全部成功</span>
              )}
            </header>
            <ul className="divide-y divide-border">
              {job.items.map((item) => (
                <CallRow
                  key={item.id}
                  item={item}
                  active={item.id === selectedId}
                  onOpen={onOpenCall}
                  primary={
                    showRoleInRow
                      ? formatRoleLabel(item.role, item.role_label)
                      : PURPOSE_LABEL[item.purpose] || item.purpose
                  }
                  secondary={
                    showRoleInRow
                      ? PURPOSE_LABEL[item.purpose] || item.purpose
                      : undefined
                  }
                />
              ))}
            </ul>
          </section>
        )
      })}
    </div>
  )
}

function RoleCallList({
  roleLabel,
  calls,
  selectedId,
  onOpenCall,
}: {
  roleLabel: string
  calls: LlmCallLogItem[]
  selectedId: string | null
  onOpenCall: (id: string) => void
}) {
  if (calls.length === 0) {
    return (
      <div className="sf-panel">
        <EmptyState title={`暂无「${roleLabel}」调用`} description="该角色尚未在本项目执行过。" />
      </div>
    )
  }

  const callFail = calls.filter((c) => c.status !== 'success').length
  const callOkPersistFail = calls.filter(
    (c) =>
      c.status === 'success' && (c.job_status === 'failed' || c.job_status === 'disabled'),
  ).length
  const persistOk = calls.filter((c) => c.job_status === 'completed').length

  return (
    <section className="overflow-hidden rounded-xl border border-border bg-surface shadow-panel">
      <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border px-5 py-3">
        <div>
          <h3 className="text-sm font-semibold text-ink">{roleLabel}</h3>
          <p className="mt-0.5 text-[11px] text-ink-faint">
            共 {calls.length} 次模型调用 · 按时间倒序
          </p>
        </div>
        <div className="text-right text-xs">
          {persistOk > 0 ? (
            <div className="text-emerald-700">{persistOk} 次已落库</div>
          ) : null}
          {callOkPersistFail > 0 ? (
            <div className="text-amber-800">{callOkPersistFail} 次调用成功但未落库</div>
          ) : null}
          {callFail > 0 ? <div className="text-red-600">{callFail} 次调用失败</div> : null}
          {persistOk === 0 && callOkPersistFail === 0 && callFail === 0 ? (
            <span className="text-ink-muted">暂无终态统计</span>
          ) : null}
        </div>
      </header>
      <ul className="divide-y divide-border">
        {calls.map((item, index) => (
          <CallRow
            key={item.id}
            item={item}
            active={item.id === selectedId}
            onOpen={onOpenCall}
            primary={index === 0 ? '最近一次' : `往前第 ${index} 次`}
            secondary={PURPOSE_LABEL[item.purpose] || item.purpose}
            metaExtra={item.job_id ? `任务 ${shortId(item.job_id, 8)}` : '无任务'}
          />
        ))}
      </ul>
    </section>
  )
}

function CallRow({
  item,
  active,
  onOpen,
  primary,
  secondary,
  metaExtra,
}: {
  item: LlmCallLogItem
  active: boolean
  onOpen: (id: string) => void
  primary: string
  secondary?: string
  metaExtra?: string
}) {
  const callOk = item.status === 'success'
  const outcome = classifyJobOutcome(item)
  return (
    <li>
      <button
        type="button"
        onClick={() => onOpen(item.id)}
        className={cn(
          'flex w-full items-center gap-3 px-5 py-3.5 text-left transition',
          active ? 'bg-action/5' : 'hover:bg-canvas-muted/60',
        )}
      >
        <StatusDot ok={callOk} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <span className="text-sm font-medium text-ink">{primary}</span>
            {secondary ? <span className="text-xs text-ink-muted">{secondary}</span> : null}
            <span
              className={cn(
                'text-[11px] font-medium',
                callOk ? 'text-emerald-700' : 'text-red-600',
              )}
            >
              {callOk ? '模型调用成功' : '模型调用失败'}
            </span>
          </div>
          <div className="mt-0.5 text-[11px] text-ink-faint">
            {formatClock(item.created_at)}
            {metaExtra ? ` · ${metaExtra}` : ''}
            {item.model_name ? ` · ${item.model_name}` : ''}
            {!callOk && item.error_message ? ` · ${item.error_message.slice(0, 80)}` : ''}
          </div>
          {outcome ? (
            <div className={cn('mt-1 text-[11px]', OUTCOME_TONE_CLASS[outcome.tone])}>
              {outcome.label}
              {outcome.tone === 'warn' && item.job_error_message ? (
                <span className="mt-0.5 block text-[10px] text-ink-faint line-clamp-2">
                  {item.job_error_message}
                </span>
              ) : null}
            </div>
          ) : null}
        </div>
        <div className="shrink-0 text-right text-xs text-ink-muted">
          <div>{formatLatency(item.latency_ms)}</div>
          <div className="text-ink-faint">
            {item.total_tokens != null ? `${item.total_tokens} tok` : '—'}
          </div>
        </div>
      </button>
    </li>
  )
}

function DetailDrawer({
  detail,
  loading,
  error,
  tab,
  onTabChange,
  onClose,
}: {
  detail?: LlmCallLogDetail
  loading: boolean
  error: unknown
  tab: DetailTab
  onTabChange: (tab: DetailTab) => void
  onClose: () => void
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <button
        type="button"
        className="absolute inset-0 bg-ink/30"
        aria-label="关闭详情"
        onClick={onClose}
      />
      <aside className="relative flex h-full w-full max-w-[28rem] flex-col border-l border-border bg-surface shadow-panel">
        <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-ink">调用详情</h2>
            {detail ? (
              <p className="mt-1 truncate text-xs text-ink-muted">
                {formatRoleLabel(detail.role, detail.role_label)} ·{' '}
                {PURPOSE_LABEL[detail.purpose] || detail.purpose}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            className="rounded-lg p-1.5 text-ink-muted hover:bg-canvas-muted hover:text-ink"
            onClick={onClose}
            aria-label="关闭"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {loading ? (
          <div className="p-5">
            <LoadingBlock label="加载详情…" />
          </div>
        ) : error ? (
          <div className="p-5">
            <ErrorBanner message={formatApiError(error)} />
          </div>
        ) : detail ? (
          <>
            <div className="flex gap-1 border-b border-border px-3 pt-2">
              {(
                [
                  { id: 'meta' as const, label: '概要' },
                  { id: 'system' as const, label: 'System' },
                  { id: 'user' as const, label: 'User' },
                  { id: 'response' as const, label: '回复' },
                ] as const
              ).map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => onTabChange(t.id)}
                  className={cn(
                    'rounded-t-md px-3 py-2 text-xs font-medium transition',
                    tab === t.id
                      ? 'bg-surface text-action shadow-[0_-1px_0_0_var(--border)_inset]'
                      : 'text-ink-muted hover:text-ink',
                  )}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-5">
              {tab === 'meta' ? <MetaPanel detail={detail} /> : null}
              {tab === 'system' ? <PromptBody content={detail.system_prompt} /> : null}
              {tab === 'user' ? <PromptBody content={detail.user_prompt} /> : null}
              {tab === 'response' ? (
                <div className="space-y-3">
                  {detail.error_message ? (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">
                      {detail.error_message}
                    </div>
                  ) : null}
                  <PromptBody content={detail.response_text} />
                </div>
              ) : null}
            </div>
          </>
        ) : null}
      </aside>
    </div>
  )
}

function MetaPanel({ detail }: { detail: LlmCallLogDetail }) {
  const outcome = classifyJobOutcome(detail)
  const primary: Array<[string, string]> = [
    ['模型调用', detail.status === 'success' ? '成功' : '失败'],
    [
      '工作台任务',
      detail.job_status
        ? JOB_STATUS_LABEL[detail.job_status] ?? detail.job_status
        : '—',
    ],
    ['项目', detail.project_title?.trim() || (detail.project_id ? shortId(detail.project_id, 12) : '—')],
    ['角色', formatRoleLabel(detail.role, detail.role_label)],
    ['用途', PURPOSE_LABEL[detail.purpose] || detail.purpose],
    ['耗时', formatLatency(detail.latency_ms)],
    ['模型', detail.model_name || '—'],
  ]
  const secondary: Array<[string, string]> = [
    ['角色 ID', detail.role || '—'],
    ['任务', shortId(detail.job_id, 12)],
    ['HTTP', detail.http_status != null ? String(detail.http_status) : '—'],
    ['Prompt Tokens', detail.prompt_tokens != null ? String(detail.prompt_tokens) : '—'],
    ['Completion Tokens', detail.completion_tokens != null ? String(detail.completion_tokens) : '—'],
    ['Total Tokens', detail.total_tokens != null ? String(detail.total_tokens) : '—'],
    ['时间', formatClock(detail.created_at)],
  ]
  return (
    <div className="space-y-5">
      {outcome ? (
        <div
          className={cn(
            'rounded-lg border px-3 py-2 text-xs',
            outcome.tone === 'ok'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
              : outcome.tone === 'warn'
                ? 'border-amber-200 bg-amber-50 text-amber-900'
                : outcome.tone === 'bad'
                  ? 'border-red-200 bg-red-50 text-red-800'
                  : 'border-border bg-canvas-muted text-ink-muted',
          )}
        >
          <p className="font-medium">{outcome.label}</p>
          {detail.job_error_message ? (
            <p className="mt-1 whitespace-pre-wrap opacity-90">{detail.job_error_message}</p>
          ) : null}
        </div>
      ) : null}
      <dl className="space-y-2.5 text-sm">
        {primary.map(([k, v]) => (
          <div key={k} className="flex items-start justify-between gap-3 border-b border-border/60 pb-2">
            <dt className="shrink-0 text-ink-faint">{k}</dt>
            <dd className="min-w-0 break-all text-right font-medium text-ink">{v}</dd>
          </div>
        ))}
      </dl>
      <dl className="space-y-2 text-xs">
        {secondary.map(([k, v]) => (
          <div key={k} className="flex items-start justify-between gap-3">
            <dt className="shrink-0 text-ink-faint">{k}</dt>
            <dd className="min-w-0 break-all text-right text-ink-muted">{v}</dd>
          </div>
        ))}
      </dl>
      {detail.error_message ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">
          {detail.error_message}
        </div>
      ) : null}
    </div>
  )
}

function PromptBody({ content }: { content?: string | null }) {
  const [expanded, setExpanded] = useState(false)
  const text = content || '（空）'
  const long = text.length > 1200
  return (
    <div>
      <pre className="whitespace-pre-wrap rounded-lg border border-border bg-canvas-muted p-3 text-xs leading-relaxed text-ink">
        {expanded || !long ? text : `${text.slice(0, 1200)}…`}
      </pre>
      {long ? (
        <button
          type="button"
          className="mt-2 text-xs text-action hover:underline"
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? '收起' : '展开全文'}
        </button>
      ) : null}
    </div>
  )
}
