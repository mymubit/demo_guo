import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { dramaApi } from '@/services/drama'
import type { LlmCallLogDetail } from '@/services/admin'
import { formatApiError } from '@/services/errors'
import { formatRoleLabel } from '@/utils/roleLabels'
import { cn } from '@/utils/cn'

const PURPOSE_LABEL: Record<string, string> = {
  artifact_generation: '角色产物',
  quality_scoring: '质量评分',
  compliance_check: '合规检查',
  connectivity_test: '连通测试',
  quality_scoring_json_repair: '评分纠错',
  compliance_check_json_repair: '合规纠错',
}

type DetailTab = 'system' | 'user' | 'response'

function purposeLabel(purpose: string): string {
  return PURPOSE_LABEL[purpose] || purpose
}

function formatLatency(ms: number | null | undefined): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

function CallLogCard({ item, defaultOpen = false }: { item: LlmCallLogDetail; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  const [tab, setTab] = useState<DetailTab>('user')
  const body =
    tab === 'system'
      ? item.system_prompt || '（空）'
      : tab === 'user'
        ? item.user_prompt || '（空）'
        : item.response_text || '（空）'

  return (
    <div className="rounded-lg border border-border bg-surface">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-start gap-2 px-3 py-3 text-left hover:bg-canvas-muted"
      >
        <span className="mt-0.5 text-ink-muted">
          {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2 text-sm font-medium text-ink">
            <span>
              #{item.seq_in_job} {formatRoleLabel(item.role)}
            </span>
            <span className="text-xs font-normal text-ink-muted">
              {purposeLabel(item.purpose)}
            </span>
            <span
              className={cn(
                'rounded px-1.5 py-0.5 text-[11px] font-medium',
                item.status === 'success'
                  ? 'bg-emerald-50 text-emerald-800'
                  : 'bg-rose-50 text-rose-800',
              )}
            >
              {item.status === 'success' ? '成功' : '失败'}
            </span>
          </span>
          <span className="mt-0.5 block text-xs text-ink-muted">
            {item.model_name || '模型未记录'} · {formatLatency(item.latency_ms)}
            {item.total_tokens ? ` · ${item.total_tokens} tokens` : ''}
          </span>
        </span>
      </button>
      {open ? (
        <div className="border-t border-border px-3 pb-3 pt-2">
          <div className="mb-2 flex gap-1">
            {(
              [
                ['user', '用户输入'],
                ['system', '系统提示'],
                ['response', '模型输出'],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => setTab(key)}
                className={cn(
                  'rounded-md px-2.5 py-1 text-xs font-medium',
                  tab === key
                    ? 'bg-action text-white'
                    : 'bg-canvas-muted text-ink-muted hover:bg-canvas',
                )}
              >
                {label}
              </button>
            ))}
          </div>
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-md bg-canvas p-3 text-xs leading-relaxed text-ink">
            {body}
          </pre>
        </div>
      ) : null}
    </div>
  )
}

function emptyStateMessage(jobStatus?: string): string {
  if (jobStatus === 'completed') {
    return '本任务无 LLM 日志记录；请确认 Celery worker 已加载写日志代码并重新评测'
  }
  if (jobStatus === 'failed') {
    return '暂无调用日志。若评分/合规调用已成功，可在下方尝试「用已有结果重新解析」。'
  }
  return '暂无调用日志。任务运行中或排队时，LLM 调用完成后将在此显示。'
}

/** 任务级 LLM 原始输入/输出（评审记录页内嵌，不依赖管理员页） */
export function JobLlmCallLogsPanel({
  jobId,
  jobStatus,
}: {
  jobId: string
  jobStatus?: string
}) {
  const query = useQuery({
    queryKey: ['job-llm-logs', jobId],
    queryFn: () => dramaApi.getJobLlmLogs(jobId, { detail: true, limit: 50 }),
    enabled: Boolean(jobId),
  })

  const items = (query.data?.items ?? []) as LlmCallLogDetail[]

  return (
    <section id="job-llm-logs" className="sf-panel space-y-4 p-5">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-ink">调用日志</h3>
          <p className="mt-0.5 text-xs text-ink-muted">
            查看本任务原始系统提示、用户输入与模型输出
          </p>
        </div>
        <Button
          size="sm"
          variant="secondary"
          iconLeft={<RefreshCw className="h-3.5 w-3.5" />}
          loading={query.isFetching}
          onClick={() => void query.refetch()}
        >
          刷新
        </Button>
      </div>
      {query.isError ? <ErrorBanner message={formatApiError(query.error)} /> : null}
      {query.isLoading ? <LoadingBlock label="加载调用日志…" /> : null}
      {!query.isLoading && !query.isError && items.length === 0 ? (
        <p className="text-sm text-ink-muted">{emptyStateMessage(jobStatus)}</p>
      ) : null}
      {items.length > 0 ? (
        <div className="space-y-2">
          {items.map((item, index) => (
            <CallLogCard key={item.id} item={item} defaultOpen={index === 0} />
          ))}
        </div>
      ) : null}
    </section>
  )
}
