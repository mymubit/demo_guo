import { describe, it, expect } from 'vitest'
import { normalizeWorkDetail } from '@/services/adapters/businessAdapters'

describe('Works detail intelligent analysis data', () => {
  it('exposes review and marketing from fusion snapshot', () => {
    const work = normalizeWorkDetail({
      project_id: 'p-1',
      title: '测试',
      status: 'completed',
      fusion_snapshot: {
        scoreReport: { overallScore: 88, grade: 'A' },
        reviewReport: { passed: true, issues: ['节奏略快'] },
        marketingKit: { titles: ['标题A'] },
      },
    })
    expect(work.scoreReport.overallScore).toBe(88)
    expect(work.reviewReport.passed).toBe(true)
    expect(work.marketingKit.titles).toEqual(['标题A'])
  })
})
