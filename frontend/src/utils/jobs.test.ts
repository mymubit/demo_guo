import { describe, expect, it } from 'vitest'
import { isSuccessfulJob, isTerminalJobStatus } from '@/utils/jobs'

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
})
