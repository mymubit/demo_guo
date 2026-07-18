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
