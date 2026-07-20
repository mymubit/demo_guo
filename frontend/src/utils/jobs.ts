import type { GenerationJob } from '@/types/domain'

/** 与后端 GENERATION_JOB_STALE_SECONDS 默认对齐：LLM 读超时 900s + 600s ≈ 25 分钟 */
export const STALE_JOB_MS = 25 * 60 * 1000

export function isTerminalJobStatus(status: GenerationJob['status']): boolean {
  return status === 'completed' || status === 'failed' || status === 'disabled'
}

/** Only completed counts as success — failed/disabled must not trigger success handlers. */
export function isSuccessfulJob(status: GenerationJob['status']): boolean {
  return status === 'completed'
}

/** 合并同 job 状态：终态优先，避免「面板已失败、父级仍 running」 */
export function mergeGenerationJob(
  prev: GenerationJob | null | undefined,
  next: GenerationJob,
): GenerationJob {
  if (!prev || prev.job_id !== next.job_id) return next
  if (isTerminalJobStatus(next.status)) return next
  if (isTerminalJobStatus(prev.status)) return prev
  return { ...prev, ...next }
}

export function isJobInFlight(status: GenerationJob['status'] | null | undefined): boolean {
  return status === 'pending' || status === 'queued' || status === 'running'
}

/** 进行中任务是否已超过合理时长（worker 可能已死）。 */
export function isStaleInFlightJob(
  job: Pick<GenerationJob, 'status' | 'updated_at' | 'created_at'> | null | undefined,
  nowMs: number = Date.now(),
  thresholdMs: number = STALE_JOB_MS,
): boolean {
  if (!job || !isJobInFlight(job.status)) return false
  const iso = job.updated_at || job.created_at
  if (!iso) return false
  const ts = Date.parse(iso)
  if (Number.isNaN(ts)) return false
  return nowMs - ts >= thresholdMs
}
