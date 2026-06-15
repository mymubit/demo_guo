export const PRICING_GROUPS = [
  { key: 'pipeline', label: '主链 Agent', prefix: 'pipeline.node.' },
  { key: 'creation', label: '创作提交', prefix: 'creation.' },
  { key: 'ai', label: '字段 AI', prefix: 'ai.generate.' },
  { key: 'other', label: '其他', prefix: '' },
]

export function groupPricing(rows) {
  const used = new Set()
  const groups = PRICING_GROUPS.map((g) => {
    const items = rows.filter((r) => {
      if (used.has(r.id)) return false
      if (g.key === 'other') {
        const matched = PRICING_GROUPS.some(
          (x) => x.key !== 'other' && r.action_key?.startsWith(x.prefix)
        )
        return !matched
      }
      if (!r.action_key?.startsWith(g.prefix)) return false
      used.add(r.id)
      return true
    })
    items.forEach((r) => used.add(r.id))
    return { ...g, items }
  })
  return groups.filter((g) => g.items.length > 0)
}
