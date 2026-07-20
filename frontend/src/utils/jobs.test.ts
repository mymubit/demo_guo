import { describe, expect, it } from 'vitest'
import {
  isJobInFlight,
  isStaleInFlightJob,
  isSuccessfulJob,
  isTerminalJobStatus,
  mergeGenerationJob,
} from '@/utils/jobs'
import type { GenerationJob } from '@/types/domain'

function job(partial: Partial<GenerationJob> & Pick<GenerationJob, 'status'>): GenerationJob {
  return {
    job_id: 'j1',
    project_id: 'p1',
    job_type: 'generation',
    progress: 0,
    ...partial,
  } as GenerationJob
}

describe('job status helpers', () => {
  it('recognizes terminal backend job statuses', () => {
    expect(isTerminalJobStatus('completed')).toBe(true)
    expect(isTerminalJobStatus('disabled')).toBe(true)
    expect(isTerminalJobStatus('failed')).toBe(true)
    expect(isTerminalJobStatus('running')).toBe(false)
  })

  it('treats only completed as success — failed/disabled are not success', () => {
    expect(isSuccessfulJob('completed')).toBe(true)
    expect(isSuccessfulJob('disabled')).toBe(false)
    expect(isSuccessfulJob('failed')).toBe(false)
    expect(isSuccessfulJob('running')).toBe(false)
  })

  it('detects in-flight jobs', () => {
    expect(isJobInFlight('running')).toBe(true)
    expect(isJobInFlight('failed')).toBe(false)
  })

  it('prefers terminal status when merging same job', () => {
    const running = job({ status: 'running', progress: 40 })
    const failed = job({ status: 'failed', progress: 0, error: 'timeout' })
    expect(mergeGenerationJob(running, failed).status).toBe('failed')
    expect(mergeGenerationJob(failed, running).status).toBe('failed')
  })

  it('detects stale in-flight jobs by updated_at', () => {
    const now = Date.parse('2026-07-17T15:00:00Z')
    const fresh = job({
      status: 'running',
      updated_at: '2026-07-17T14:50:00Z',
    })
    const stale = job({
      status: 'running',
      updated_at: '2026-07-17T10:00:00Z',
    })
    expect(isStaleInFlightJob(fresh, now)).toBe(false)
    expect(isStaleInFlightJob(stale, now)).toBe(true)
    expect(isStaleInFlightJob(job({ status: 'failed', updated_at: '2026-07-17T10:00:00Z' }), now)).toBe(
      false,
    )
  })
})
