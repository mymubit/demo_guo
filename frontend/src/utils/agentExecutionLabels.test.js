import { describe, expect, it } from 'vitest'
import { runStatusLabel, RUN_STATUS_LABELS } from './agentExecutionLabels'

describe('runStatusLabel', () => {
  it('maps completed status to Chinese label', () => {
    expect(runStatusLabel('completed')).toBe('成功')
  })

  it('maps running status to Chinese label', () => {
    expect(runStatusLabel('running')).toBe('执行中')
  })

  it('maps partial status to Chinese label', () => {
    expect(runStatusLabel('partial')).toBe('部分成功')
  })

  it('falls back to raw status for unknown values', () => {
    expect(runStatusLabel('custom')).toBe('custom')
  })

  it('covers all defined run status keys', () => {
    for (const key of Object.keys(RUN_STATUS_LABELS)) {
      expect(runStatusLabel(key)).toBe(RUN_STATUS_LABELS[key])
    }
  })
})
