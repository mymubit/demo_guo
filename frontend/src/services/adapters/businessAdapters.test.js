import { describe, it, expect } from 'vitest'
import { normalizeMembership, normalizeOrder, normalizeWorkItem, normalizeWorkDetail } from './businessAdapters'

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

describe('normalizeWorkDetail', () => {
  it('maps fusion_snapshot snake_case fields to view props', () => {
    const out = normalizeWorkDetail({
      project_id: 'p-2',
      title: '详情作品',
      status: 'ready',
      overall_score: 90,
      grade: 'A',
      fusion_snapshot: {
        score_report: { overallScore: 90, grade: 'A' },
        gate_summary: { passed: 8, total: 10 },
        review_report: { passed: true, issues: [] },
        marketing_kit: { titles: ['宣发标题'] },
        project_brief: { working_title: '测试剧' },
      },
    })
    expect(out.scoreReport.overallScore).toBe(90)
    expect(out.gateSummary.passed).toBe(8)
    expect(out.reviewReport.passed).toBe(true)
    expect(out.marketingKit.titles).toEqual(['宣发标题'])
    expect(out.projectBrief.working_title).toBe('测试剧')
  })
})
