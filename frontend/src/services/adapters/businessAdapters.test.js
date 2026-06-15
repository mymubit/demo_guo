import { describe, it, expect } from 'vitest'
import { normalizeMembership, normalizeOrder, normalizeWorkItem } from './businessAdapters'

describe('normalizeMembership', () => {
  it('maps plan and wallet fields', () => {
    const out = normalizeMembership({
      is_active: true,
      is_expired: false,
      end_at: '2026-12-31T00:00:00Z',
      plan: { name: '月卡', grant_coins: 20 },
      wallet: { currency_name: '创作币', balance: 100 },
    })
    expect(out.plan_name).toBe('月卡')
    expect(out.wallet.balance).toBe(100)
    expect(out.is_active).toBe(true)
    expect(out.end_at).toBe('2026-12-31T00:00:00Z')
  })

  it('returns null for empty input', () => {
    expect(normalizeMembership(null)).toBeNull()
  })
})

describe('normalizeOrder', () => {
  it('extracts plan name from nested membership_plan', () => {
    const out = normalizeOrder({
      order_no: 'SF001',
      membership_plan: { name: '年卡' },
    })
    expect(out.plan_name).toBe('年卡')
  })
})

describe('normalizeWorkItem', () => {
  it('normalizes project fields and status', () => {
    const out = normalizeWorkItem({
      project_id: 'p-1',
      title: '测试作品',
      status: 'completed',
      episode_count: 12,
      created_at: '2026-06-15T10:00:00Z',
      core_idea: '  核心创意  ',
    })
    expect(out.project_id).toBe('p-1')
    expect(out.episodes).toBe(12)
    expect(out.idea).toBe('核心创意')
    expect(out.createdAt).toBeTruthy()
  })
})
