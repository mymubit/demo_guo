import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { FilterEmptyState } from '@/components/layout/FilterEmptyState'
import { ListPageToolbar } from '@/components/layout/ListPageToolbar'
import { OpsPageShell } from '@/components/ops/OpsPageShell'
import { CallDetailDrawer } from '@/components/ops/llmLogs/CallDetailDrawer'
import { JobTimeline } from '@/components/ops/llmLogs/JobTimeline'
import { ProjectSidebar } from '@/components/ops/llmLogs/ProjectSidebar'
import {
  groupByProject,
  matchWorkbenchFilter,
  ROLE_FILTER_OPTIONS,
  type DetailTab,
  type ProjectGroup,
} from '@/components/ops/llmLogs/llmLogUtils'
import { adminApi } from '@/services/admin'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'

export function LlmLogsPage() {
  const [params, setParams] = useSearchParams()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [activeProjectKey, setActiveProjectKey] = useState<string | null>(null)
  const [highlightJobKey, setHighlightJobKey] = useState<string | null>(null)
  const [detailTab, setDetailTab] = useState<DetailTab>('meta')
  const [benchFilter, setBenchFilter] = useState(() => params.get('bench') || '')
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

  const items = useMemo(() => {
    const raw = listQuery.data?.items ?? []
    if (!benchFilter) return raw
    return raw.filter((item) => matchWorkbenchFilter(item, benchFilter))
  }, [listQuery.data?.items, benchFilter])

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

  return (
    <OpsPageShell
      title="LLM 调用"
      description="按项目查看生成与质检的模型调用链；点一行打开原文详情。"
      actions={
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
      }
      toolbar={
        <ListPageToolbar
          filters={[
            {
              id: 'role',
              label: '角色',
              value: filters.role ?? '',
              onChange: (value) => patchFilter('role', value),
              options: [
                { value: '', label: '全部' },
                ...ROLE_FILTER_OPTIONS.map((opt) => ({ value: opt.value, label: opt.label })),
              ],
            },
            {
              id: 'status',
              label: '调用结果',
              value: filters.status ?? '',
              onChange: (value) => patchFilter('status', value),
              options: [
                { value: '', label: '全部' },
                { value: 'success', label: '成功' },
                { value: 'failed', label: '失败' },
              ],
            },
            {
              id: 'bench',
              label: '工作台',
              value: benchFilter,
              onChange: (value) => {
                setBenchFilter(value)
                patchFilter('bench', value)
              },
              options: [
                { value: '', label: '全部' },
                { value: 'persisted', label: '已落库' },
                { value: 'bench_warn', label: '落库异常' },
                { value: 'bench_fail', label: '任务失败' },
                { value: 'no_job', label: '无任务' },
              ],
            },
          ]}
          actions={
            <label className="flex items-center gap-2 text-sm text-ink-muted">
              任务 ID
              <input
                className="sf-control w-44 py-1.5 font-mono text-xs"
                value={filters.job_id ?? ''}
                placeholder="可选，支持深链"
                onChange={(e) => patchFilter('job_id', e.target.value.trim())}
              />
            </label>
          }
        />
      }
    >
      {listQuery.isLoading ? <LoadingBlock label="加载中…" /> : null}
      {listQuery.isError ? <ErrorBanner message={formatApiError(listQuery.error)} /> : null}

      {!listQuery.isLoading && !listQuery.isError ? (
        projectGroups.length === 0 ? (
          <FilterEmptyState
            title="暂无调用记录"
            description="跑一次生成或模型连通测试后，会按项目出现在这里。"
            variant="inbox"
          />
        ) : (
          <div className="grid min-h-[32rem] gap-5 xl:grid-cols-[17rem_minmax(0,1fr)]">
            <ProjectSidebar
              groups={projectGroups}
              activeKey={activeProject?.key ?? null}
              onSelect={selectProject}
            />
            <main className="min-w-0">
              {activeProject ? (
                <JobTimeline
                  group={activeProject}
                  highlightJobKey={highlightJobKey}
                  selectedId={selectedId}
                  jobRefs={jobRefs}
                  onOpenCall={setSelectedId}
                />
              ) : (
                <div className="sf-panel">
                  <EmptyState title="请选择项目" description="从左侧选择一个项目查看调用时间线。" />
                </div>
              )}
            </main>
          </div>
        )
      ) : null}

      {selectedId ? (
        <CallDetailDrawer
          detail={detailQuery.data}
          loading={detailQuery.isLoading}
          error={detailQuery.error}
          tab={detailTab}
          onTabChange={setDetailTab}
          onClose={() => setSelectedId(null)}
        />
      ) : null}
    </OpsPageShell>
  )
}
