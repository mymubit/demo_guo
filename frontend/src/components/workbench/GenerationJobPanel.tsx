import { useEffect, useRef, useState } from 'react'
import { Button } from '@/components/ui/Button'
import { ErrorBanner } from '@/components/ui/Tabs'
import { Badge } from '@/components/ui/Badge'
import { GenerationTroubleCard } from '@/components/workbench/GenerationTroubleCard'
import { dramaApi } from '@/services/drama'
import { subscribeJobEvents } from '@/services/sse'
import { formatApiError } from '@/services/errors'
import { isSuccessfulJob } from '@/utils/jobs'
import type { GenerationJob, SseJobEvent } from '@/types/domain'

const STATUS_LABEL: Record<string, string> = {
  pending: '等待中',
  queued: '排队中',
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  disabled: '已禁用',
}

const EVENT_TYPE_LABEL: Record<string, string> = {
  status: '状态',
  progress: '进度',
  log: '日志',
  message: '消息',
  error: '错误',
  warning: '警告',
  artifact: '产物',
  done: '完成',
  heartbeat: '心跳',
}

function summarizeEventData(data: Record<string, unknown>): string {
  const parts: string[] = []
  for (const [key, value] of Object.entries(data)) {
    if (value == null) continue
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      parts.push(`${key}=${value}`)
    }
  }
  return parts.slice(0, 4).join(' · ')
}

export function GenerationJobPanel({
  projectId,
  job,
  onCompleted,
}: {
  projectId: string | null
  job: GenerationJob | null
  onCompleted?: (job: GenerationJob) => void
}) {
  const [events, setEvents] = useState<SseJobEvent[]>([])
  const [transportError, setTransportError] = useState<string | null>(null)
  const [status, setStatus] = useState(job?.status)
  const [progress, setProgress] = useState(job?.progress ?? 0)
  const [jobError, setJobError] = useState<string | null>(job?.error ?? null)
  const onCompletedRef = useRef(onCompleted)
  onCompletedRef.current = onCompleted

  useEffect(() => {
    if (!job?.job_id) return

    setEvents([])
    setTransportError(null)
    setStatus(job.status)
    setProgress(job.progress ?? 0)
    setJobError(job.error ?? null)

    const stop = subscribeJobEvents(projectId, job.job_id, {
      onEvent: (event) => {
        setEvents((prev) => [...prev.slice(-49), event])
        if (event.status) setStatus(event.status)
        if (typeof event.progress === 'number') setProgress(event.progress)
        if (event.message && (event.type === 'error' || event.status === 'failed')) {
          setJobError(event.message)
        }
      },
      onDone: () => {
        const refresh = projectId
          ? dramaApi.getGenerationStatus(projectId, job.job_id)
          : dramaApi.getJob(job.job_id)
        void refresh
          .then((latest) => {
            setStatus(latest.status)
            if (typeof latest.progress === 'number') setProgress(latest.progress)
            if (latest.error) setJobError(latest.error)
            // failed / disabled must not be treated as success
            if (isSuccessfulJob(latest.status)) {
              onCompletedRef.current?.(latest)
            }
          })
          .catch((err) => setTransportError(formatApiError(err)))
      },
      onError: (err) => setTransportError(formatApiError(err)),
    })

    return stop
    // Only re-subscribe when job identity or project changes — not on status/progress
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: avoid duplicate SSE
  }, [job?.job_id, projectId])

  if (!job) return null

  const badgeTone =
    status === 'completed'
      ? 'success'
      : status === 'failed'
        ? 'danger'
        : status === 'running'
          ? 'brand'
          : status === 'disabled'
            ? 'warning'
            : 'default'

  const clamped = Math.min(100, Math.max(0, progress))
  const showTrouble = status === 'failed' || status === 'disabled'

  return (
    <section className="sf-panel p-4" aria-label="生成任务进度">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-ink">生成任务</h4>
          <p className="mt-1 font-mono text-xs text-ink-muted">{job.job_id}</p>
        </div>
        <Badge tone={badgeTone}>{STATUS_LABEL[status ?? ''] ?? status}</Badge>
      </div>
      <div
        className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="生成进度"
      >
        <div className="h-full bg-brand-500 transition-all" style={{ width: `${clamped}%` }} />
      </div>
      <div className="sr-only" aria-live="polite">
        进度 {clamped}% · {STATUS_LABEL[status ?? ''] ?? status}
      </div>
      {transportError ? (
        <div className="mt-3">
          <ErrorBanner message={transportError} />
        </div>
      ) : null}
      {showTrouble ? (
        <div className="mt-3">
          <GenerationTroubleCard message={jobError} status={status} />
        </div>
      ) : null}
      <ul className="mt-3 max-h-40 space-y-1 overflow-auto text-xs text-ink-muted" aria-live="polite">
        {events.map((e, idx) => (
          <li key={`${e.type}-${idx}`}>
            [{EVENT_TYPE_LABEL[e.type] ?? e.type}]{' '}
            {e.message ||
              (e.data && typeof e.data === 'object'
                ? summarizeEventData(e.data as Record<string, unknown>)
                : '')}
          </li>
        ))}
      </ul>
      <div className="mt-3">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => {
            const refresh = projectId
              ? dramaApi.getGenerationStatus(projectId, job.job_id)
              : dramaApi.getJob(job.job_id)
            void refresh.then((latest) => {
              setStatus(latest.status)
              if (typeof latest.progress === 'number') setProgress(latest.progress)
              if (latest.error) setJobError(latest.error)
              if (isSuccessfulJob(latest.status)) onCompletedRef.current?.(latest)
            })
          }}
        >
          刷新状态
        </Button>
      </div>
    </section>
  )
}
