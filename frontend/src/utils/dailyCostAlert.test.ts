import { describe, expect, it } from 'vitest'
import {
  getShanghaiDateString,
  isDailyCostOverAlert,
  parseEstimatedCost,
} from './dailyCostAlert'

describe('dailyCostAlert utils', () => {
  it('formats Shanghai calendar date as YYYY-MM-DD', () => {
    // UTC 2026-07-22 16:30 → Asia/Shanghai 2026-07-23
    const date = new Date('2026-07-22T16:30:00.000Z')
    expect(getShanghaiDateString(date)).toBe('2026-07-23')
  })

  it('parses estimated cost strings', () => {
    expect(parseEstimatedCost('12.5')).toBe(12.5)
    expect(parseEstimatedCost(null)).toBeNull()
    expect(parseEstimatedCost('')).toBeNull()
    expect(parseEstimatedCost('x')).toBeNull()
  })

  it('alerts only when cost strictly exceeds threshold', () => {
    expect(isDailyCostOverAlert(10, 5)).toBe(true)
    expect(isDailyCostOverAlert(5, 5)).toBe(false)
    expect(isDailyCostOverAlert(1, null)).toBe(false)
    expect(isDailyCostOverAlert(null, 1)).toBe(false)
  })
})
