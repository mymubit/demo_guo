import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import {
  CheckCircle2,
  FileSearch,
  RefreshCw,
  RotateCcw,
  Trash2,
  XCircle,
} from 'lucide-react'
import { ReportArtifactView } from '@/components/artifacts/ArtifactViews'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { PageShell } from '@/components/layout/PageShell'
import { GenerationJobPanel } from '@/components/workbench/GenerationJobPanel'
import { JobLlmCallLogsPanel } from '@/components/workbench/JobLlmCallLogsPanel'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { cn } from '@/utils/cn'
import { isSuccessfulJob } from '@/utils/jobs'
import type { GenerationJob, GenerationJobStatus } from '@/types/domain'

const STATUS_LABEL: Record<string, string> = {
  pending: '等待中',
  queued: '排队中',
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  disabled: '已禁用',
}

function formatTime(iso: string | null | undefined): string {
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

function shortId(id: string, len = 8): string {
  return id.length <= len ? id : id.slice(0, len)
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }
  return null
}

function reviewReports(job: GenerationJob | null): {
  quality: Record<string, unknown> | null
  compliance: Record<string, unknown> | null
  overallScore: string | null
  grade: string | null
} {
  const result = asRecord(job?.result)
  if (!result) {
    return { quality: null, compliance: null, overallScore: null, grade: null }
  }
  const quality = asRecord(result.quality_report)
  return {
    quality,
    compliance: asRecord(result.compliance_report),
    overallScore: quality?.overall_score != null ? String(quality.overall_score) : null,
    grade: quality?.grade != null ? String(quality.grade) : null,
  }
}

function statusTone(
  status: GenerationJobStatus | undefined,
): 'success' | 'danger' | 'warning' | 'default' {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'running' || status === 'queued' || status === 'pending') return 'warning'
  return 'default'
}

export function ExternalReviewRecordsPage() {
  const [params, setParams] = useSearchParams()
  const jobFromUrl = params.get('job')
  const [selectedId, setSelectedId] = useState<string | null>(jobFromUrl)
  const [statusFilter, setStatusFilter] = useState<string>('')

  const listQuery = useQuery({
    queryKey: ['external-script-reviews'],
    queryFn: () => dramaApi.listExternalScriptReviews({ limit: 50 }),
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? []
      const hasActive = items.some(
        (item) =>
          item.status === 'queued' || item.status === 'running' || item.status === 'pending',
      )
      return hasActive ? 4000 : false
    },
  })

  const items = useMemo(() => {
    const all = listQuery.data?.items ?? []
    if (!statusFilter) return all
    return all.filter((item) => item.status === statusFilter)
  }, [listQuery.data?.items, statusFilter])

  useEffect(() => {
    if (jobFromUrl) {
      setSelectedId(jobFromUrl)
      return
    }
    if (!selectedId && items.length > 0) {
      setSelectedId(items[0].job_id)
    }
  }, [jobFromUrl, items, selectedId])

  const selected = useMemo(
    () => items.find((item) => item.job_id === selectedId) ?? null,
    [items, selectedId],
  )

  const detailQuery = useQuery({
    queryKey: ['external-script-review', selectedId],
    queryFn: () => dramaApi.getJob(selectedId!),
    enabled: Boolean(selectedId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'queued' || status === 'running' || status === 'pending') return 3000
      return false
    },
  })

  const [job, setJob] = useState<GenerationJob | null>(null)

  useEffect(() => {
    if (detailQuery.data) {
      setJob(detailQuery.data)
      return
    }
    setJob(selected)
  }, [detailQuery.data, selected])

  const { quality, compliance } = reviewReports(job)

  const reprocessMutation = useMutation({
    mutationFn: (jobId: string) => dramaApi.reprocessJob(jobId),
    onSuccess: (latest) => {
      setJob(latest)
      void listQuery.refetch()
      void detailQuery.refetch()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => dramaApi.deleteJob(jobId),
    onSuccess: (_data, deletedId) => {
      const remaining = (listQuery.data?.items ?? []).filter((item) => item.job_id !== deletedId)
      void listQuery.refetch().then((result) => {
        const nextItems = result.data?.items ?? remaining
        const nextId = nextItems[0]?.job_id ?? null
        setSelectedId(nextId)
        setJob(null)
        const next = new URLSearchParams(params)
        if (nextId) next.set('job', nextId)
        else next.delete('job')
        setParams(next, { replace: true })
      })
    },
  })

  function handleDelete(target: GenerationJob) {
    const label = target.title || target.source_filename || shortId(target.job_id)
    const ok = window.confirm(
      `确认删除「${label}」？\n将删除该条评测记录与结果，且不可恢复。`,
    )
    if (!ok) return
    deleteMutation.mutate(target.job_id)
  }

  const canDelete =
    job != null &&
    job.status !== 'pending' &&
    job.status !== 'queued' &&
    job.status !== 'running'

  function selectJob(jobId: string) {
    setSelectedId(jobId)
    const next = new URLSearchParams(params)
    next.set('job', jobId)
    setParams(next, { replace: true })
  }

  return (
    <PageShell
      title="评审记录"
      description="查看外部剧本评测历史、任务进度与评分/合规报告"
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <Link
            to="/tools/script-review"
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink hover:bg-canvas-muted/60"
          >
            <FileSearch className="h-4 w-4" />
            发起评测
          </Link>
          <label className="flex items-center gap-2 text-sm text-ink-muted">
            状态
            <select
              className="sf-control w-auto py-1.5"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">全部</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
              <option value="running">运行中</option>
              <option value="queued">排队中</option>
            </select>
          </label>
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
        </div>
      }
    >
      {listQuery.isError ? <ErrorBanner message={formatApiError(listQuery.error)} /> : null}
      {deleteMutation.isError ? (
        <ErrorBanner message={formatApiError(deleteMutation.error)} />
      ) : null}

      <div className="grid min-h-[32rem] gap-4 lg:grid-cols-[22rem_minmax(0,1fr)]">
        <aside className="sf-panel flex flex-col overflow-hidden">
          <div className="border-b border-border px-4 py-3 text-sm font-medium text-ink-muted">
            最近记录
            <span className="ml-2 text-xs font-normal text-ink-faint">{items.length}</span>
          </div>
          {listQuery.isLoading ? (
            <div className="p-4">
              <LoadingBlock label="加载记录…" />
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-center">
              <p className="text-sm text-ink-muted">暂无评测记录</p>
              <Link
                to="/tools/script-review"
                className="text-sm font-medium text-action underline-offset-2 hover:underline"
              >
                去发起评测
              </Link>
            </div>
          ) : (
            <ul className="flex-1 overflow-auto">
              {items.map((item) => {
                const active = item.job_id === selectedId
                const reports = reviewReports(item)
                return (
                  <li key={item.job_id} className="border-b border-border last:border-b-0">
                    <button
                      type="button"
                      onClick={() => selectJob(item.job_id)}
                      className={cn(
                        'flex w-full flex-col gap-1.5 px-4 py-3 text-left transition',
                        active ? 'bg-action/5' : 'hover:bg-canvas-muted/60',
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 font-medium text-ink">
                          <div className="truncate" title={item.title || item.source_filename || undefined}>
                            {item.title || item.source_filename || `未命名评测 · ${shortId(item.job_id)}`}
                          </div>
                          {item.source_filename &&
                          item.title &&
                          item.source_filename !== item.title ? (
                            <div className="mt-0.5 truncate text-[11px] font-normal text-ink-faint">
                              {item.source_filename}
                            </div>
                          ) : null}
                        </div>
                        <Badge tone={statusTone(item.status)} className="shrink-0">
                          {STATUS_LABEL[item.status] ?? item.status}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between gap-2 text-xs text-ink-muted">
                        <span>{formatTime(item.updated_at)}</span>
                        <span className="font-mono text-[11px] text-ink-faint">
                          {shortId(item.job_id)}
                        </span>
                      </div>
                      {reports.overallScore || reports.grade ? (
                        <div className="flex items-center gap-2 text-xs text-ink">
                          {reports.overallScore ? (
                            <span className="inline-flex items-center gap-1">
                              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                              总分 {reports.overallScore}
                            </span>
                          ) : null}
                          {reports.grade ? <span>等级 {reports.grade}</span> : null}
                        </div>
                      ) : item.status === 'failed' ? (
                        <div className="inline-flex items-center gap-1 text-xs text-rose-700">
                          <XCircle className="h-3.5 w-3.5" />
                          <span className="truncate">{item.error || item.message || '评测失败'}</span>
                        </div>
                      ) : null}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </aside>

        <section className="min-w-0 space-y-4">
          {!selectedId ? (
            <div className="sf-panel flex min-h-[20rem] items-center justify-center p-8 text-sm text-ink-muted">
              选择左侧一条记录查看详情
            </div>
          ) : detailQuery.isError ? (
            <ErrorBanner message={formatApiError(detailQuery.error)} />
          ) : !job ? (
            <LoadingBlock label="加载详情…" />
          ) : (
            <>
              <GenerationJobPanel
                projectId={null}
                job={job}
                onJobUpdate={(latest: GenerationJob) => {
                  setJob(latest)
                  void listQuery.refetch()
                }}
                onCompleted={(latest: GenerationJob) => {
                  setJob(latest)
                  void listQuery.refetch()
                }}
              />
              <JobLlmCallLogsPanel jobId={job.job_id} jobStatus={job.status} />
              {job.status === 'failed' ? (
                <div className="sf-panel space-y-3 p-4">
                  <p className="text-sm text-ink-muted">
                    若调用日志里评分/合规已成功返回，可直接用已有结果重新解析落库，无需再调模型。
                  </p>
                  {reprocessMutation.isError ? (
                    <ErrorBanner message={formatApiError(reprocessMutation.error)} />
                  ) : null}
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      iconLeft={<RotateCcw className="h-3.5 w-3.5" />}
                      loading={reprocessMutation.isPending}
                      onClick={() => reprocessMutation.mutate(job.job_id)}
                    >
                      用已有结果重新解析
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      iconLeft={<Trash2 className="h-3.5 w-3.5" />}
                      loading={deleteMutation.isPending}
                      disabled={!canDelete}
                      onClick={() => handleDelete(job)}
                    >
                      删除记录
                    </Button>
                  </div>
                </div>
              ) : canDelete ? (
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    variant="danger"
                    iconLeft={<Trash2 className="h-3.5 w-3.5" />}
                    loading={deleteMutation.isPending}
                    onClick={() => handleDelete(job)}
                  >
                    删除记录
                  </Button>
                </div>
              ) : null}
              {isSuccessfulJob(job.status) && (quality || compliance) ? (
                <div className="space-y-4">
                  {quality ? <ReportArtifactView kind="quality_report" data={quality} /> : null}
                  {compliance ? (
                    <ReportArtifactView kind="compliance_report" data={compliance} />
                  ) : null}
                </div>
              ) : null}
            </>
          )}
        </section>
      </div>
    </PageShell>
  )
}
