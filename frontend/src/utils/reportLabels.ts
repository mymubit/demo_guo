/** 质检/合规报告展示用中文标签 */

export const QUALITY_DIMENSION_LABEL_ZH: Record<string, string> = {
  format: '格式规范',
  narrative: '叙事效率',
  conflict: '冲突处理',
  character: '角色一致性',
  emotion: '情感深度',
  logic: '逻辑一致性',
  satisfaction: '爽点密度',
  hooks: '钩子强度',
  paywall: '付费点优化',
  genre_fit: '赛道匹配',
}

export const COMPLIANCE_RISK_TYPE_LABEL_ZH: Record<string, string> = {
  p0: 'P0 阻断',
  p1: 'P1 高风险',
  p2: 'P2 留意',
}

export function qualityDimensionLabelZh(key: string): string {
  return QUALITY_DIMENSION_LABEL_ZH[key] || key
}

export function complianceRiskTypeLabelZh(value: unknown): string {
  const key = String(value ?? '')
    .trim()
    .toLowerCase()
  return COMPLIANCE_RISK_TYPE_LABEL_ZH[key] || (key ? key.toUpperCase() : '风险项')
}

/** 将阻断项对象整理为可读中文段落，避免直接 JSON.stringify */
export function formatComplianceIssueZh(item: unknown): {
  title: string
  detail: string
  meta: string[]
} {
  if (item == null) {
    return { title: '未命名问题', detail: '', meta: [] }
  }
  if (typeof item === 'string') {
    const text = item.trim()
    return { title: text || '未命名问题', detail: '', meta: [] }
  }
  if (typeof item !== 'object' || Array.isArray(item)) {
    return { title: String(item), detail: '', meta: [] }
  }
  const row = item as Record<string, unknown>
  const detail = String(row.description ?? row.detail ?? row.summary ?? '').trim()
  const title =
    String(row.title ?? row.name ?? row.issue ?? row.rule_key ?? row.category ?? '')
      .trim() ||
    (detail.length > 32 ? `${detail.slice(0, 32)}…` : detail) ||
    '未命名问题'
  const meta: string[] = []
  const level = String(row.level ?? row.severity ?? row.type ?? '').trim()
  if (level) {
    const levelKey = level.toLowerCase()
    meta.push(
      `等级 ${COMPLIANCE_RISK_TYPE_LABEL_ZH[levelKey] || level.toUpperCase()}`,
    )
  }
  const category = String(row.category ?? row.type_name ?? '').trim()
  if (category && category !== title) meta.push(`类别 ${category}`)
  const episodes = row.affected_episodes ?? row.episodes
  if (Array.isArray(episodes) && episodes.length > 0) {
    meta.push(`涉及集数 ${episodes.map(String).join('、')}`)
  } else if (typeof episodes === 'string' && episodes.trim()) {
    meta.push(`涉及集数 ${episodes.trim()}`)
  }
  const suggestion = String(row.suggestion ?? row.fix ?? '').trim()
  if (suggestion) meta.push(`建议 ${suggestion}`)
  return { title, detail, meta }
}
