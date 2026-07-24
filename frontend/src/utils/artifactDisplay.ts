/** 产物展示可读化：避免把 JSON/dict 结构原样甩给用户。 */

import {
  axisFieldLabelZh,
  localizeDisplayValue,
} from '@/utils/themeLabels'

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

/** 常见产物字段中文标签（未知键避免裸英文 snake_case） */
export const ARTIFACT_FIELD_LABELS: Record<string, string> = {
  title: '标题',
  drama_title: '剧名',
  name: '名称',
  summary: '摘要',
  overview: '概览',
  short: '短梗概',
  full: '完整梗概',
  core_idea: '核心创意',
  core_premise: '核心前提',
  core_conflict: '核心冲突',
  core_event: '核心事件',
  hook_concept: '钩子概念',
  selling_point: '卖点',
  commercial_hook: '商业钩子',
  target_audience: '目标受众',
  audience_channel: '受众频道',
  audience_identification: '观众代入点',
  logline: '一句话故事',
  genre_matrix: '题材矩阵',
  genre_fit: '题材契合度',
  rule_params: '叙事节奏设定',
  episode_count: '集数',
  episode_duration: '单集时长（分钟）',
  episode_number: '集序号',
  episode: '集',
  first_episode_hook: '首集钩子',
  opening_hook: '开场钩子',
  ending_hook: '收尾钩子',
  paywall: '付费卡点',
  paywall_hook: '付费钩子',
  paywall_direction: '付费墙方向',
  paywall_distribution: '付费墙分布',
  market_opportunity: '市场机会',
  differentiation_strategy: '差异化策略',
  blockbuster_factors: '爆款因子',
  compliance_risk: '合规风险',
  reference_works: '参考作品',
  competitor_references: '对标作品',
  inspiration: '可借鉴',
  avoidance: '需规避',
  characters: '角色',
  character: '角色',
  character_system: '人物体系',
  character_states: '角色状态',
  world: '时空背景',
  world_system: '世界观',
  world_rules: '世界规则',
  setting_summary: '设定摘要',
  root_rules: '根本规则',
  power_structure: '权力结构',
  emotion: '主情绪',
  emotion_curve: '全剧情绪走势',
  emotion_intensity: '情绪强度',
  emotion_nodes: '情绪节点',
  emotion_pace: '情绪节奏',
  series_emotion_curve: '全剧情绪曲线',
  identity: '主角身份',
  conflict: '主冲突',
  conflict_escalation_chain: '冲突升级链',
  goal_conflict: '目标冲突',
  protagonist_structure: '主角结构',
  flavor_tags: '风味标签',
  production_plan: '制作计划',
  production_notes: '制作备注',
  storyboard: '分镜',
  visual_assets: '视觉资产',
  marketing_assets: '营销资产',
  release_checklist: '发布清单',
  hook: '钩子',
  hooks: '钩子列表',
  hook_types: '钩子类型',
  hook_grade: '钩子等级',
  synopsis: '剧情梗概',
  beat_sheet: '节拍表',
  complexity_band: '复杂度',
  complexity_score: '复杂度得分',
  episodes: '分集',
  scenes: '场次',
  scene_count: '场次数',
  dialogue: '对白',
  dialogue_ratio: '对白占比',
  description: '说明',
  notes: '备注',
  adapt_source: '改编来源',
  mode: '模式',
  retained: '保留项',
  enhanced: '强化项',
  rewritten: '重写项',
  originality_check: '原创性检查',
  relationship_map: '关系图谱',
  relationship_changes: '关系变化',
  series_structure: '系列结构',
  main_storyline: '主线',
  six_stage_structure: '六幕结构',
  major_reversal_positions: '重大反转点',
  foreshadowing: '伏笔',
  foreshadowing_table: '伏笔表',
  role_type: '角色类型',
  surface_desire: '外在欲望',
  deep_need: '内在需求',
  ghost: '心结',
  lie: '自我谎言',
  flaw: '性格缺陷',
  arc: '人物弧光',
  start: '起点',
  turning_point_1: '转折一',
  turning_point_2: '转折二',
  end: '终局',
  voice_tag: '语言标签',
  visual_anchor: '视觉锚点',
  reversal: '反转',
  reversal_density: '反转频率',
  act_ratio: '六阶段篇幅占比',
  setup: '铺垫',
  payoff: '回收',
  satisfaction: '爽点',
  satisfaction_points: '爽点列表',
  golden_lines: '金句',
  plot_pace: '情节节奏',
  rhythm_state: '节奏状态',
  rhythm_tag: '节奏标签',
  grade: '等级',
  score: '得分',
  overall_score: '总分',
  overall_result: '总评',
  verdict: '判定',
  verdict_detail: '判定说明',
  dimensions: '维度',
  weight: '权重',
  deductions: '扣分项',
  defects: '缺陷',
  issues: '问题',
  remaining_issues: '遗留问题',
  resolved_issues: '已解决问题',
  blocking_issues: '阻断问题',
  blocking_items: '阻断项',
  risk_items: '风险项',
  suggestion: '建议',
  revision_summary: '修订摘要',
  revision_priorities: '修订优先级',
  revision_route: '修订路径',
  needs_revision: '需要修订',
  can_continue_next_batch: '可继续下一批',
  can_release: '可发布',
  pass_threshold: '及格线',
  format: '格式',
  format_check: '格式检查',
  logic: '逻辑',
  narrative: '叙事',
  script: '剧本',
  word_count: '字数',
  tags: '标签',
  type: '类型',
  result: '结果',
  evidence: '依据',
  budget_range: '预算区间',
  cost_drivers: '成本驱动',
  high_cost_scenes: '高成本场次',
  lower_cost_alternatives: '低成本替代',
  interactive_adaptation: '互动改编',
  missing_materials: '缺失材料',
  next_episode_constraints: '下集约束',
  continuity_summary: '连续性摘要',
  prop_states: '道具状态',
  active_clues: '活跃线索',
  memory_checkpoint: '记忆检查点',
  episode_narrative_designs: '分集叙事设计',
  episode_tp: '分集转折点',
  episode_et: '分集情绪点',
  episode_ev: '分集事件点',
  target_platform: '目标平台',
  scoring_preset: '评分预设',
  check_mode: '检查模式',
  checked_artifact: '检查产物',
  scored_artifact: '评分产物',
  source_artifact: '来源产物',
  resolved_script_key: '解析剧本键',
  evolution_proposal: '进化提案',
  pricing_context: '定价上下文',
  platform_policy_version: '平台政策版本',
  platform_policy_verified_at: '政策核验时间',
  policy_version: '政策版本',
  verified_at: '核验时间',
  config_revision: '配置修订号',
}

/** 六阶段名称（与 series-scale.stage_order 对齐） */
const SIX_STAGE_LABELS = ['开篇', '升温', '高点', '转折', '冲刺', '结局'] as const

function formatPercent(ratio: number): string {
  const pct = Math.round(ratio * 1000) / 10
  return Number.isInteger(pct) ? `${pct}%` : `${pct}%`
}

function formatReversalDensity(raw: unknown): string {
  const n = typeof raw === 'number' ? raw : Number(raw)
  if (!Number.isFinite(n)) return formatLeaf(raw, 'reversal_density')
  const pct = formatPercent(n)
  let level = '适中'
  if (n < 0.2) level = '偏疏'
  else if (n < 0.35) level = '适中'
  else if (n < 0.5) level = '偏密'
  else level = '很密'
  return `${pct}（${level}）· 约每 10 集有 ${Math.round(n * 10)} 次明显反转`
}

function formatEmotionCurve(raw: unknown): string {
  if (!Array.isArray(raw) || raw.length === 0) return ''
  const nums = raw
    .map((item) => (typeof item === 'number' ? item : Number(item)))
    .filter((n) => Number.isFinite(n))
  if (nums.length === 0) return ''
  const path = nums.join(' → ')
  const min = Math.min(...nums)
  const max = Math.max(...nums)
  return `${path}\n（1=情绪最冷，10=最热；本剧最低 ${min}、最高 ${max}）`
}

function formatActRatio(raw: unknown): string {
  if (!Array.isArray(raw) || raw.length === 0) return ''
  const lines: string[] = []
  raw.forEach((item, index) => {
    const n = typeof item === 'number' ? item : Number(item)
    if (!Number.isFinite(n)) return
    const stage = SIX_STAGE_LABELS[index] ?? `阶段 ${index + 1}`
    lines.push(`${stage} ${formatPercent(n)}`)
  })
  if (lines.length === 0) return ''
  return `${lines.join(' · ')}\n（全剧按这六段分配集数比重）`
}

function buildRuleParamsSection(value: unknown): ArtifactDisplaySection | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  const obj = value as Record<string, unknown>
  const rows: Array<{ label: string; value: string }> = []

  if (obj.reversal_density != null) {
    rows.push({ label: '反转频率', value: formatReversalDensity(obj.reversal_density) })
  }
  if (obj.emotion_curve != null) {
    const text = formatEmotionCurve(obj.emotion_curve)
    if (text) rows.push({ label: '全剧情绪走势', value: text })
  }
  if (obj.act_ratio != null) {
    const text = formatActRatio(obj.act_ratio)
    if (text) rows.push({ label: '六阶段篇幅占比', value: text })
  }
  if (Array.isArray(obj.hook_types) && obj.hook_types.length > 0) {
    const hooks = obj.hook_types
      .map((item) => formatLeaf(item, 'hook_types'))
      .filter((t) => t && !isPlaceholder(t))
    if (hooks.length) rows.push({ label: '钩子类型', value: hooks.join('、') })
  }

  // 其余未知字段仍展出，避免丢内容
  for (const [key, child] of Object.entries(obj)) {
    if (['reversal_density', 'emotion_curve', 'act_ratio', 'hook_types'].includes(key)) continue
    if (shouldSkipKey(key)) continue
    if (child == null) continue
    if (typeof child !== 'object') {
      const text = formatLeaf(child, key)
      if (text && !isPlaceholder(text)) rows.push({ label: labelForKey(key), value: text })
    }
  }

  if (rows.length === 0) return null
  return {
    id: 'rule_params',
    title: '叙事节奏设定',
    hint: '由题材矩阵自动合成，用来约束后面结构与节奏；不必手改。',
    rows,
  }
}

function buildCompetitorSection(value: unknown): ArtifactDisplaySection | null {
  if (!Array.isArray(value) || value.length === 0) return null
  const cards: Array<{ title: string; rows: Array<{ label: string; value: string }> }> = []

  value.forEach((item, index) => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) {
      const text = formatLeaf(item, 'competitor_references')
      if (text) cards.push({ title: `参考 ${index + 1}`, rows: [{ label: '说明', value: text }] })
      return
    }
    const obj = item as Record<string, unknown>
    const title =
      asDisplayText(obj.title) ||
      asDisplayText(obj.name) ||
      asDisplayText(obj.work) ||
      `对标作品 ${index + 1}`
    const rows: Array<{ label: string; value: string }> = []
    const inspiration = asDisplayText(obj.inspiration ?? obj.learn ?? obj.takeaway)
    const avoidance = asDisplayText(obj.avoidance ?? obj.avoid ?? obj.pitfall)
    if (inspiration && !isPlaceholder(inspiration)) {
      rows.push({ label: '可借鉴', value: inspiration })
    }
    if (avoidance && !isPlaceholder(avoidance)) {
      rows.push({ label: '需规避', value: avoidance })
    }
    for (const [key, child] of Object.entries(obj)) {
      if (['title', 'name', 'work', 'inspiration', 'learn', 'takeaway', 'avoidance', 'avoid', 'pitfall'].includes(key)) {
        continue
      }
      if (shouldSkipKey(key) || child == null || typeof child === 'object') continue
      const text = formatLeaf(child, key)
      if (text && !isPlaceholder(text)) rows.push({ label: labelForKey(key), value: text })
    }
    if (rows.length === 0 && !isPlaceholder(title)) {
      rows.push({ label: '说明', value: '已列入对标，但未写明借鉴/规避点。' })
    }
    cards.push({ title, rows })
  })

  if (cards.length === 0) return null
  return {
    id: 'competitor_references',
    title: '对标作品',
    hint: '同赛道可参考的片子：学它的优点，避开它的雷区。',
    variant: 'cards',
    rows: [],
    cards,
  }
}

/** 对创作者无意义的技术键：可读预览中跳过 */
const SKIP_KEYS = new Set([
  'theme_code',
  'matrix_key',
  'schema_version',
  'artifact_key',
  'preset_theme_code',
  'id',
  'pk',
  'uuid',
  'created_at',
  'updated_at',
  'schema',
  'raw',
])

export type ArtifactDisplayEntry = {
  path: string
  label: string
  value: string
}

export type ArtifactDisplaySection = {
  id: string
  title: string
  /** 章节说明，帮助理解区块用途 */
  hint?: string
  /** cards：竞品等条目型内容 */
  variant?: 'default' | 'cards'
  rows: Array<{ label: string; value: string }>
  cards?: Array<{ title: string; rows: Array<{ label: string; value: string }> }>
}


/** 未知 snake_case 键按词素拼中文，避免「surface desire」类英文标签 */
const KEY_TOKEN_ZH: Record<string, string> = {
  surface: '外在',
  desire: '欲望',
  deep: '内在',
  need: '需求',
  ghost: '心结',
  lie: '谎言',
  flaw: '缺陷',
  arc: '弧光',
  voice: '语言',
  tag: '标签',
  visual: '视觉',
  anchor: '锚点',
  role: '角色',
  ending: '收尾',
  opening: '开场',
  hook: '钩子',
  paywall: '付费墙',
  episode: '分集',
  scene: '场次',
  emotion: '情绪',
  curve: '曲线',
  nodes: '节点',
  intensity: '强度',
  pace: '节奏',
  rhythm: '节奏',
  plot: '情节',
  story: '故事',
  line: '线',
  main: '主',
  series: '系列',
  structure: '结构',
  stage: '幕',
  six: '六',
  conflict: '冲突',
  escalation: '升级',
  chain: '链',
  major: '重大',
  reversal: '反转',
  positions: '位置',
  distribution: '分布',
  foreshadowing: '伏笔',
  table: '表',
  setting: '设定',
  summary: '摘要',
  root: '根本',
  rules: '规则',
  power: '权力',
  world: '世界',
  adapt: '改编',
  source: '来源',
  mode: '模式',
  short: '短',
  full: '完整',
  originality: '原创性',
  check: '检查',
  relationship: '关系',
  map: '图谱',
  changes: '变化',
  identification: '代入',
  audience: '观众',
  commercial: '商业',
  market: '市场',
  opportunity: '机会',
  differentiation: '差异化',
  strategy: '策略',
  blockbuster: '爆款',
  factors: '因子',
  compliance: '合规',
  risk: '风险',
  reference: '参考',
  works: '作品',
  competitor: '竞品',
  references: '参考',
  production: '制作',
  plan: '计划',
  notes: '备注',
  assets: '资产',
  marketing: '营销',
  release: '发布',
  checklist: '清单',
  complexity: '复杂度',
  band: '档位',
  score: '得分',
  grade: '等级',
  overall: '总体',
  result: '结果',
  verdict: '判定',
  detail: '说明',
  revision: '修订',
  priorities: '优先级',
  route: '路径',
  needs: '需要',
  can: '可否',
  continue: '继续',
  next: '下一',
  batch: '批次',
  count: '数量',
  number: '序号',
  duration: '时长',
  ratio: '比例',
  density: '密度',
  act: '幕次',
  word: '字',
  dialogue: '对白',
  golden: '金',
  lines: '句',
  satisfaction: '爽点',
  points: '点',
  setup: '铺垫',
  payoff: '回收',
  active: '活跃',
  clues: '线索',
  prop: '道具',
  states: '状态',
  continuity: '连续性',
  constraints: '约束',
  missing: '缺失',
  materials: '材料',
  blocking: '阻断',
  issues: '问题',
  items: '项',
  remaining: '遗留',
  resolved: '已解决',
  suggestion: '建议',
  evidence: '依据',
  weight: '权重',
  deductions: '扣分',
  defects: '缺陷',
  format: '格式',
  logic: '逻辑',
  narrative: '叙事',
  designs: '设计',
  memory: '记忆',
  checkpoint: '检查点',
  budget: '预算',
  range: '区间',
  cost: '成本',
  drivers: '驱动',
  high: '高',
  lower: '低',
  alternatives: '替代',
  interactive: '互动',
  adaptation: '改编',
  target: '目标',
  platform: '平台',
  scoring: '评分',
  preset: '预设',
  policy: '政策',
  version: '版本',
  verified: '核验',
  at: '时间',
  config: '配置',
  pricing: '定价',
  context: '上下文',
  evolution: '进化',
  proposal: '提案',
  turning: '转折',
  point: '点',
  start: '起点',
  end: '终局',
  first: '首',
  direction: '方向',
  concept: '概念',
  idea: '创意',
  premise: '前提',
  event: '事件',
  title: '标题',
  name: '名称',
  description: '说明',
  tags: '标签',
  type: '类型',
}

function composeKeyLabelZh(key: string): string {
  const parts = key
    .toLowerCase()
    .split(/[_-]+/)
    .map((p) => p.trim())
    .filter(Boolean)
  if (parts.length === 0) return ''
  const mapped = parts.map((p) => KEY_TOKEN_ZH[p] || '')
  if (mapped.every(Boolean)) return mapped.join('')
  return ''
}

function labelForKey(key: string): string {
  if (ARTIFACT_FIELD_LABELS[key]) return ARTIFACT_FIELD_LABELS[key]
  const axis = axisFieldLabelZh(key)
  if (axis !== key) return axis
  if (/^\d+$/.test(key)) return `第 ${key} 项`
  const composed = composeKeyLabelZh(key)
  if (composed) return composed
  // 仍未知时不回退英文空格化，统一用中性标签
  return '其他信息'
}

function formatLeaf(value: unknown, fieldHint?: string): string {
  const localized = localizeDisplayValue(value, fieldHint)
  if (localized) return localized
  // 本地化后为空时，仍保留非占位原文，避免把 JSON 里的内容吞掉
  if (typeof value === 'string') {
    const text = value.trim()
    if (text && !isPlaceholder(text)) return text
  }
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return ''
}

function shouldSkipKey(key: string): boolean {
  if (SKIP_KEYS.has(key)) return true
  if (key.endsWith('_id') || key.endsWith('_ids')) return true
  if (key.startsWith('_')) return true
  return false
}

/**
 * 将产物整理为分组章节（中文标题 + 中文值），供可读预览使用。
 * 默认完整展开，不截断数组、不因深度把内容丢掉。
 */
export function buildArtifactSections(
  payload: unknown,
  options?: { maxDepth?: number; maxRows?: number },
): ArtifactDisplaySection[] {
  const maxDepth = options?.maxDepth ?? 12
  const maxRows = options?.maxRows ?? 2000
  const sections: ArtifactDisplaySection[] = []
  let rowCount = 0

  const pushRow = (section: ArtifactDisplaySection, label: string, value: string) => {
    if (rowCount >= maxRows) return
    if (!value || isPlaceholder(value)) return
    section.rows.push({ label, value })
    rowCount += 1
  }

  const ensureSection = (id: string, title: string): ArtifactDisplaySection => {
    let section = sections.find((s) => s.id === id)
    if (!section) {
      section = { id, title, rows: [] }
      sections.push(section)
    }
    return section
  }

  const walkObject = (
    obj: Record<string, unknown>,
    sectionId: string,
    sectionTitle: string,
    depth: number,
  ) => {
    const section = ensureSection(sectionId, sectionTitle)
    for (const [key, value] of Object.entries(obj)) {
      if (rowCount >= maxRows) return
      if (shouldSkipKey(key)) continue
      const label = labelForKey(key)

      if (value == null) continue
      if (typeof value !== 'object') {
        pushRow(section, label, formatLeaf(value, key))
        continue
      }

      if (Array.isArray(value)) {
        if (value.length === 0) continue
        const primitives = value.every(
          (item) => item == null || ['string', 'number', 'boolean'].includes(typeof item),
        )
        if (primitives) {
          const preview = value
            .map((item) => formatLeaf(item, key))
            .filter((t) => t && !isPlaceholder(t))
            .join('、')
          pushRow(section, label, preview || `共 ${value.length} 项`)
        } else {
          value.forEach((item, index) => {
            if (rowCount >= maxRows) return
            if (!item || typeof item !== 'object' || Array.isArray(item)) {
              pushRow(section, `${label} · ${index + 1}`, formatLeaf(item, key))
              return
            }
            if (depth < maxDepth) {
              walkObject(
                item as Record<string, unknown>,
                `${sectionId}.${key}.${index}`,
                `${label}（${index + 1}）`,
                depth + 1,
              )
            } else {
              // 极深嵌套：仍尽量展平一层字段，避免整块丢失
              const flat = item as Record<string, unknown>
              for (const [childKey, childVal] of Object.entries(flat)) {
                if (shouldSkipKey(childKey)) continue
                if (childVal == null || typeof childVal === 'object') continue
                pushRow(
                  section,
                  `${label}（${index + 1}）· ${labelForKey(childKey)}`,
                  formatLeaf(childVal, childKey),
                )
              }
            }
          })
        }
        continue
      }

      if (depth < maxDepth) {
        walkObject(value as Record<string, unknown>, `${sectionId}.${key}`, label, depth + 1)
      } else {
        // 极深对象：展平一层叶子，不再丢给「请看 JSON」
        for (const [childKey, childVal] of Object.entries(value as Record<string, unknown>)) {
          if (shouldSkipKey(childKey)) continue
          if (childVal == null || typeof childVal === 'object') continue
          pushRow(section, `${label} · ${labelForKey(childKey)}`, formatLeaf(childVal, childKey))
        }
      }
    }
  }

  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    if (payload != null && typeof payload !== 'object') {
      const basic = ensureSection('basic', '内容')
      pushRow(basic, '内容', formatLeaf(payload))
    }
    return sections.filter((s) => s.rows.length > 0)
  }

  const root = payload as Record<string, unknown>
  const summary = ensureSection('summary', '概要')
  for (const [key, value] of Object.entries(root)) {
    if (shouldSkipKey(key)) continue
    if (key === 'rule_params') {
      const special = buildRuleParamsSection(value)
      if (special) sections.push(special)
      continue
    }
    if (key === 'competitor_references') {
      const special = buildCompetitorSection(value)
      if (special) sections.push(special)
      continue
    }
    const label = labelForKey(key)
    if (value == null) continue
    if (typeof value !== 'object') {
      pushRow(summary, label, formatLeaf(value, key))
      continue
    }
    if (Array.isArray(value)) {
      if (value.length === 0) continue
      const primitives = value.every(
        (item) => item == null || ['string', 'number', 'boolean'].includes(typeof item),
      )
      if (primitives) {
        const preview = value
          .map((item) => formatLeaf(item, key))
          .filter((t) => t && !isPlaceholder(t))
          .join('、')
        pushRow(summary, label, preview || `共 ${value.length} 项`)
      } else {
        walkObject({ [key]: value }, key, label, 0)
      }
      continue
    }
    walkObject(value as Record<string, unknown>, key, label, 1)
  }

  return sections.filter(
    (s) => s.rows.length > 0 || (s.cards != null && s.cards.length > 0),
  )
}

/** 兼容旧调用；优先使用 buildArtifactSections */
export function flattenArtifactEntries(
  payload: unknown,
  options?: { maxDepth?: number; maxEntries?: number },
): ArtifactDisplayEntry[] {
  const sections = buildArtifactSections(payload, {
    maxDepth: options?.maxDepth,
    maxRows: options?.maxEntries,
  })
  const out: ArtifactDisplayEntry[] = []
  for (const section of sections) {
    for (const row of section.rows) {
      out.push({
        path: `${section.id}.${row.label}`,
        label: section.id === 'summary' ? row.label : `${section.title} · ${row.label}`,
        value: row.value,
      })
    }
  }
  return out
}

export function formatArtifactJson(payload: unknown): string {
  try {
    return JSON.stringify(payload ?? {}, null, 2)
  } catch {
    return String(payload)
  }
}
