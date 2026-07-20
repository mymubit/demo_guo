/** 产物展示可读化：避免把 JSON/dict 结构原样甩给用户。 */

const PLACEHOLDER_RE = /^(待补充|暂无|未命名|N\/?A|—|-|null|undefined)$/i

export function isPlaceholder(value: unknown): boolean {
  if (value == null) return true
  if (typeof value === 'string') {
    const text = value.trim()
    return !text || PLACEHOLDER_RE.test(text) || text.startsWith('待补充')
  }
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value as object).length === 0
  return false
}

export function asDisplayText(value: unknown): string {
  if (value == null) return ''
  if (typeof value === 'string') return value.trim()
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return ''
}

/** 尝试把 JSON / Python dict 字符串解析成结构 */
export function parseLooseStructure(raw: unknown): unknown {
  if (raw == null) return null
  if (typeof raw === 'object') return raw
  if (typeof raw !== 'string') return null
  const text = raw.trim()
  if (!text) return null
  if (!(text.startsWith('{') || text.startsWith('['))) return null

  try {
    return JSON.parse(text) as unknown
  } catch {
    // Python repr：单引号、None/True/False
    try {
      const jsonish = text
        .replace(/\bNone\b/g, 'null')
        .replace(/\bTrue\b/g, 'true')
        .replace(/\bFalse\b/g, 'false')
        .replace(/'/g, '"')
      return JSON.parse(jsonish) as unknown
    } catch {
      return null
    }
  }
}

const CONFLICT_LABELS: Record<string, string> = {
  stage: '幕次',
  conflict_type: '冲突类型',
  description: '说明',
  type: '类型',
  name: '名称',
  summary: '摘要',
}

export function formatConflictItem(item: unknown): string {
  const parsed = typeof item === 'string' ? (parseLooseStructure(item) ?? item) : item
  if (typeof parsed === 'string') {
    const text = parsed.trim()
    return isPlaceholder(text) ? '' : text
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return ''
  const obj = parsed as Record<string, unknown>
  const stage = obj.stage
  const conflictType = asDisplayText(obj.conflict_type ?? obj.type)
  const description = asDisplayText(obj.description ?? obj.summary)
  const head = [stage != null && stage !== '' ? `第${String(stage)}幕` : '', conflictType]
    .filter(Boolean)
    .join(' · ')
  if (head && description) return `${head}：${description}`
  if (description) return description
  if (head) return head
  return formatObjectReadable(obj, CONFLICT_LABELS)
}

const RULE_PART_LABELS: Record<string, string> = {
  rule: '规则',
  trigger: '触发',
  applicable_to: '适用',
  violation_cost: '代价',
  visible_manifestation: '外显',
  name: '名称',
  description: '说明',
}

export type RootRuleParts = { title: string; details: Array<{ label: string; text: string }> }

export function formatRootRule(item: unknown): RootRuleParts | null {
  const parsed = typeof item === 'string' ? (parseLooseStructure(item) ?? item) : item

  if (typeof parsed === 'string') {
    const text = parsed.trim()
    if (!text || isPlaceholder(text)) return null
    if (text.includes('｜') || text.includes('|')) {
      const parts = text.split(/｜|\|/).map((p) => p.trim()).filter(Boolean)
      const title = parts[0] ?? text
      const details = parts.slice(1).map((part) => {
        const m = part.match(/^([^：:]+)[：:](.+)$/)
        if (m) return { label: m[1].trim(), text: m[2].trim() }
        return { label: '补充', text: part }
      })
      return { title, details }
    }
    return { title: text, details: [] }
  }

  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return null
  const obj = parsed as Record<string, unknown>
  const title =
    asDisplayText(obj.rule) ||
    asDisplayText(obj.name) ||
    asDisplayText(obj.description) ||
    ''
  if (!title || isPlaceholder(title)) return null
  const details: Array<{ label: string; text: string }> = []
  for (const [key, label] of Object.entries(RULE_PART_LABELS)) {
    if (key === 'rule' || key === 'name' || key === 'description') continue
    const text = asDisplayText(obj[key])
    if (text && !isPlaceholder(text)) details.push({ label, text })
  }
  return { title, details }
}

const ARC_KEYS: Array<{ keys: string[]; label: string }> = [
  { keys: ['start', 'initial', 'beginning'], label: '起点' },
  { keys: ['turning_point_1', 'midpoint', 'mid1'], label: '转折一' },
  { keys: ['turning_point_2', 'low_point', 'mid2'], label: '转折二' },
  { keys: ['end', 'final', 'ending'], label: '终局' },
]

export function formatArcParts(
  arc: unknown,
): Array<{ label: string; text: string }> {
  const parsed = typeof arc === 'string' ? (parseLooseStructure(arc) ?? arc) : arc
  if (typeof parsed === 'string') {
    const text = parsed.trim()
    return text && !isPlaceholder(text) ? [{ label: '弧光', text }] : []
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return []
  const obj = parsed as Record<string, unknown>
  const parts: Array<{ label: string; text: string }> = []
  for (const row of ARC_KEYS) {
    let text = ''
    for (const key of row.keys) {
      text = asDisplayText(obj[key])
      if (text && !isPlaceholder(text)) break
    }
    if (text && !isPlaceholder(text)) parts.push({ label: row.label, text })
  }
  return parts
}

export function formatObjectReadable(
  obj: Record<string, unknown>,
  labels: Record<string, string> = {},
): string {
  const chunks: string[] = []
  for (const [key, value] of Object.entries(obj)) {
    const text = asDisplayText(value)
    if (!text || isPlaceholder(text)) continue
    const label = labels[key] || key
    chunks.push(`${label}：${text}`)
  }
  return chunks.join('；')
}

export function pickMeaningfulText(...candidates: unknown[]): string {
  const structureFallbacks: string[] = []
  for (const candidate of candidates) {
    if (typeof candidate === 'string') {
      const text = candidate.trim()
      if (!text || isPlaceholder(text)) continue
      if (looksLikeRawStructure(text)) {
        const parsed = parseLooseStructure(text)
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          const readable = formatObjectReadable(parsed as Record<string, unknown>)
          if (readable) structureFallbacks.push(readable)
        }
        continue
      }
      return text
    }
    if (typeof candidate === 'number' || typeof candidate === 'boolean') {
      return String(candidate)
    }
  }
  return structureFallbacks[0] ?? ''
}

export function looksLikeRawStructure(text: string): boolean {
  const t = text.trim()
  return (
    (t.startsWith('{') && t.endsWith('}')) ||
    (t.startsWith('[') && t.endsWith(']')) ||
    /^\{'[a-z_]+':/.test(t)
  )
}
