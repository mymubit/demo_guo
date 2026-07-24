/** 题材矩阵 / 立项简报字段的中文展示解析。 */

import type { ThemeMatrix } from '@/types/workbench'

const AXIS_LABEL_ZH: Record<string, string> = {
  emotion: '主情绪',
  identity: '主角身份',
  conflict: '主冲突',
  world: '时空背景',
  audience_channel: '受众频道',
  protagonist_structure: '主角结构',
  flavor_tags: '风味标签',
}

const RISK_LABEL_ZH: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

/** 矩阵未加载时的枚举兜底（避免页面直接露出英文码） */
const OPTION_FALLBACK_ZH: Record<string, string> = {
  // 受众 / 结构
  female: '女频',
  male: '男频',
  general: '普适',
  'single-male': '大男主',
  'single-female': '大女主',
  'dual-power': '双强CP',
  bl: '双男主',
  gl: '双女主',
  'multi-female': '多女主',
  ensemble: '群像',
  // 主情绪
  revenge: '复仇爽感',
  love: '爱情甜虐',
  healing: '治愈共鸣',
  suspense: '悬疑烧脑',
  ambition: '野心逐权',
  comedy: '喜剧解压',
  justice: '正义昭雪',
  warmth: '温情烟火',
  nostalgia: '怀旧情怀',
  // 身份
  underdog: '弱势逆袭',
  reborn: '重生穿越',
  'hidden-elite': '隐藏大佬',
  ordinary: '普通人',
  outcast: '边缘异类',
  student: '青春成长',
  protector: '守护照护',
  bound: '契约绑定',
  'returning-elite': '强者归来',
  // 冲突
  family: '家族伦理',
  workplace: '职场商战',
  romance: '情感关系',
  power: '权谋斗争',
  survival: '生存危机',
  crime: '罪案追凶',
  disparity: '阶级落差',
  redemption: '救赎弥补',
  tradition: '礼教现代',
  // 时空
  modern: '都市现代',
  ancient: '古代古风',
  republic: '年代民国',
  rural: '乡土小镇',
  fantasy: '幻想异能',
  campus: '校园青春',
  scifi: '科幻未来',
  virtual: '虚拟世界',
  overseas: '异域出海',
  // 风味标签（高频）
  wuxia: '武侠江湖',
  xianxia: '修仙玄幻',
  palace: '宫斗宅斗·朝堂',
  harem: '后宫争宠',
  zhainu: '宅斗内院',
  nongtian: '种田经营',
  'war-god': '战神归来',
  'divine-doctor': '神医圣手',
  'ceo-domineering': '霸总豪门',
  'flash-marriage': '闪婚契约',
  'secret-baby': '萌宝带球',
  'angst-revenge': '打脸虐渣',
  'sweet-heavy': '高甜少虐',
  'female-awakening': '女性觉醒',
  'system-panel': '系统面板',
  'transmigration-book': '穿书穿剧',
  matrix: '题材矩阵',
  // 角色类型 / 改编模式
  protagonist: '主角',
  antagonist: '反派',
  supporting: '配角',
  original: '原创',
  adapt: '改编',
  // 复杂度 / 评级 / 判定
  standard: '标准',
  strict: '严格',
  relaxed: '宽松',
  rhythm_first: '节奏优先',
  simple: '简单',
  moderate: '适中',
  complex: '复杂',
  pass: '通过',
  fail: '未通过',
  warn: '警告',
  warning: '警告',
  blocked: '阻断',
  approved: '已通过',
  rejected: '已拒绝',
  pending: '待处理',
  candidate: '候选',
  committed: '已确认',
  draft: '草稿',
  true: '是',
  false: '否',
  yes: '是',
  no: '否',
  s: 'S 级',
  a: 'A 级',
  b: 'B 级',
  c: 'C 级',
}

/** 英文码按词素拼中文（未知枚举兜底，避免 Title Case 英文） */
const ENUM_TOKEN_ZH: Record<string, string> = {
  single: '单',
  dual: '双',
  multi: '多',
  male: '男',
  female: '女',
  power: '强',
  elite: '大佬',
  hidden: '隐藏',
  returning: '归来',
  war: '战',
  god: '神',
  divine: '神',
  doctor: '医',
  ceo: '霸总',
  domineering: '强势',
  flash: '闪',
  marriage: '婚',
  secret: '隐藏',
  baby: '萌宝',
  angst: '虐',
  revenge: '复仇',
  sweet: '甜',
  heavy: '重',
  awakening: '觉醒',
  system: '系统',
  panel: '面板',
  transmigration: '穿越',
  book: '书',
  paywall: '付费墙',
  hook: '钩子',
  cliffhanger: '悬念',
  midpoint: '中点',
  climax: '高潮',
  opening: '开场',
  ending: '收尾',
  episode: '分集',
  scene: '场次',
  character: '角色',
  world: '世界',
  story: '故事',
  emotion: '情绪',
  rhythm: '节奏',
  score: '得分',
  grade: '等级',
  risk: '风险',
  low: '低',
  medium: '中',
  high: '高',
}

/** 正文里常见英文剧本术语 / 评级词 */
const PROSE_TERM_ZH: Array<[RegExp, string]> = [
  [/\bWant\b/g, '外在欲望'],
  [/\bNeed\b/g, '内在需求'],
  [/\bGhost\b/g, '心结'],
  [/\bGoal\b/g, '目标'],
  [/\bLie\b/g, '自我谎言'],
  [/\bTruth\b/g, '内在真相'],
  [/\bStakes?\b/gi, '赌注'],
  [/\bHook\b/g, '钩子'],
  [/\bPaywall\b/gi, '付费卡点'],
  [/\bCliffhanger\b/gi, '悬念卡点'],
  [/\bLogline\b/gi, '一句话故事'],
  [/\bInciting Incident\b/gi, '激励事件'],
  [/\bMidpoint\b/gi, '中点转折'],
  [/\bClimax\b/gi, '高潮'],
  [/\bS级\b/g, '顶级'],
  [/\bA级\b/g, '优质'],
  [/\bB级\b/g, '合格'],
  [/\bCP\b/g, '搭档关系'],
  [/\bprotagonist\b/gi, '主角'],
  [/\bantagonist\b/gi, '反派'],
  [/\bsupporting\b/gi, '配角'],
]

export function axisFieldLabelZh(key: string): string {
  return AXIS_LABEL_ZH[key] ?? key
}

export function complianceRiskLabelZh(value: unknown): string {
  const key = String(value ?? '')
  return RISK_LABEL_ZH[key] ?? (OPTION_FALLBACK_ZH[key] ?? key)
}

export function resolveThemeOptionLabel(
  matrix: ThemeMatrix | null | undefined,
  axisOrField: string,
  value: string,
): string {
  if (!value) return ''
  if (axisOrField === 'flavor_tags') {
    const hit = matrix?.flavor_tags?.options?.find((o) => o.value === value)
    return hit?.label_zh || OPTION_FALLBACK_ZH[value] || value
  }
  const axis = matrix?.axes?.[axisOrField]
  const hit = axis?.options?.find((o) => o.value === value)
  return hit?.label_zh || OPTION_FALLBACK_ZH[value] || value
}

/** 展示层轻度本地化：替换剧本术语英文，不改动存库原文 */
export function localizeProseForDisplay(text: string): string {
  let out = text
  for (const [pattern, zh] of PROSE_TERM_ZH) {
    out = out.replace(pattern, zh)
  }
  return out
}

function isAsciiCodeToken(text: string): boolean {
  if (/[\u4e00-\u9fff]/.test(text)) return false
  if (/\s/.test(text)) return false
  return /^[A-Za-z][A-Za-z0-9_-]*$/.test(text)
}

/** 将 snake/kebab 英文码拼成中文；拼不出则返回空，避免露出英文码 */
function composeEnumZh(raw: string): string {
  const parts = raw
    .toLowerCase()
    .split(/[_-]+/)
    .map((p) => p.trim())
    .filter(Boolean)
  if (parts.length === 0) return ''
  const mapped = parts.map((p) => ENUM_TOKEN_ZH[p] || OPTION_FALLBACK_ZH[p] || '')
  if (mapped.every(Boolean)) return mapped.join('')
  if (parts.length === 1 && mapped[0]) return mapped[0]
  return ''
}

/**
 * 叶值展示中文化：枚举码 → 中文；合规风险 → 低/中/高；正文轻度术语替换。
 * 未知英文码尽量中文化或隐藏码感，不 Title Case 英文。
 */
export function localizeDisplayValue(value: unknown, fieldHint?: string): string {
  if (value == null) return ''
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number') return String(value)
  const text = String(value).trim()
  if (!text) return ''
  if (fieldHint === 'compliance_risk') return complianceRiskLabelZh(text)

  const lower = text.toLowerCase()
  const enumHit = OPTION_FALLBACK_ZH[text] || OPTION_FALLBACK_ZH[lower]
  if (enumHit) return enumHit

  if (isAsciiCodeToken(text)) {
    const composed = composeEnumZh(text)
    if (composed) return composed
    // 单段无映射英文码：不当作正文展示，避免「Protagonist」类噪声
    if (text.length <= 24) return ''
  }

  return localizeProseForDisplay(text)
}
