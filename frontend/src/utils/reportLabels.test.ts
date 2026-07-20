import { describe, expect, it } from 'vitest'
import {
  complianceRiskTypeLabelZh,
  formatComplianceIssueZh,
  qualityDimensionLabelZh,
} from '@/utils/reportLabels'

describe('reportLabels', () => {
  it('maps quality dimension keys to zh', () => {
    expect(qualityDimensionLabelZh('genre_fit')).toBe('赛道匹配')
    expect(qualityDimensionLabelZh('paywall')).toBe('付费点优化')
  })

  it('maps risk type to zh', () => {
    expect(complianceRiskTypeLabelZh('p2')).toBe('P2 留意')
    expect(complianceRiskTypeLabelZh('P1')).toBe('P1 高风险')
  })

  it('formats blocking issue object without raw json', () => {
    const issue = formatComplianceIssueZh({
      level: 'P1',
      title: '血腥描写过重',
      category: '暴力',
      description: '多处肢解描写缺少弱化处理',
      affected_episodes: [12, 13],
      suggestion: '弱化血腥细节',
    })
    expect(issue.title).toBe('血腥描写过重')
    expect(issue.detail).toMatch(/肢解/)
    expect(issue.meta.join(' ')).toMatch(/等级/)
    expect(issue.meta.join(' ')).toMatch(/12、13/)
    expect(JSON.stringify(issue)).not.toMatch(/"level"/)
  })

  it('falls back title from category or description', () => {
    const issue = formatComplianceIssueZh({
      category: '犯罪正义收束',
      description: '犯罪描写密集但结尾缺少法律收束',
      level: 'p1',
    })
    expect(issue.title).toBe('犯罪正义收束')
    expect(issue.detail).toMatch(/法律收束/)
  })
})
