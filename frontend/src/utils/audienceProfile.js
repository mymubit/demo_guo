/** 目标受众 — 结构化字段与 AI 解析 */

export const AUDIENCE_AGE_PRESETS = [
  '18-24岁',
  '25-34岁',
  '35-45岁',
  '45岁以上',
  '都市女性为主',
  '都市男性为主',
  '泛人群',
]

export const AUDIENCE_PREF_PRESETS = [
  '甜宠',
  '虐恋',
  '逆袭',
  '复仇',
  '悬疑',
  '豪门',
  '大女主',
  '身份反转',
  '释压爽感',
  '高智商',
]

const PREF_SYNONYMS = [
  ['打脸', '逆袭'],
  ['爽感', '释压爽感'],
  ['释压', '释压爽感'],
  ['宣泄', '释压爽感'],
  ['宠爱', '甜宠'],
  ['浪漫', '甜宠'],
  ['虐', '虐恋'],
  ['重生', '身份反转'],
  ['反转', '身份反转'],
  ['悬疑', '悬疑'],
  ['复仇', '复仇'],
  ['豪门', '豪门'],
  ['智商', '高智商'],
]

const EMPTY_PROFILE = { ageRange: '', preferences: [], note: '' }

export function stripMarkdown(text) {
  return String(text || '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .trim()
}

function splitPreferences(raw) {
  return String(raw || '')
    .split(/[、,，/|]+/)
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 8)
}

function extractPreferencesFromText(text) {
  const found = new Set()
  for (const tag of AUDIENCE_PREF_PRESETS) {
    if (text.includes(tag)) found.add(tag)
  }
  for (const [kw, tag] of PREF_SYNONYMS) {
    if (text.includes(kw)) found.add(tag)
  }
  return [...found]
}

function matchAgePreset(text) {
  const t = String(text || '')
  if (!t) return ''

  if (AUDIENCE_AGE_PRESETS.includes(t)) return t

  const range = t.match(/(\d{1,2})\s*[至到\-~—]\s*(\d{1,2})\s*岁?/)
  if (range) {
    const mid = (parseInt(range[1], 10) + parseInt(range[2], 10)) / 2
    if (mid <= 24) return '18-24岁'
    if (mid <= 34) return '25-34岁'
    if (mid <= 45) return '35-45岁'
    return '45岁以上'
  }

  if (/都市女性|女性为主|女性群体|女性用户/.test(t)) return '都市女性为主'
  if (/都市男性|男性为主|男性用户/.test(t)) return '都市男性为主'
  if (/泛人群|全年龄|大众/.test(t)) return '泛人群'

  for (const preset of AUDIENCE_AGE_PRESETS) {
    if (t.includes(preset.replace('岁', ''))) return preset
  }
  return ''
}

/** 将 AI 文本映射到可选标签 */
function applyAudienceTagMatching(profile) {
  const next = {
    ageRange: profile.ageRange || '',
    note: profile.note || '',
    preferences: [...(profile.preferences || [])],
  }
  const corpus = [next.ageRange, next.note, next.preferences.join(' ')].join(' ')

  const prefSet = new Set(next.preferences)
  for (const p of extractPreferencesFromText(corpus)) {
    if (AUDIENCE_PREF_PRESETS.includes(p)) prefSet.add(p)
  }
  next.preferences = [...prefSet]

  const matchedAge = matchAgePreset(next.ageRange) || matchAgePreset(next.note)
  if (matchedAge) {
    const ageDetail =
      next.ageRange && !AUDIENCE_AGE_PRESETS.includes(next.ageRange) ? next.ageRange : ''
    next.ageRange = matchedAge
    if (ageDetail && ageDetail !== matchedAge && !next.note.includes(ageDetail)) {
      next.note = [ageDetail, next.note].filter(Boolean).join('；')
    }
  }

  return next
}

/** 解析 AI 三行格式或整段描述 */
export function parseAudienceProfile(text) {
  const profile = { ...EMPTY_PROFILE, preferences: [] }
  const cleaned = stripMarkdown(text)
  if (!cleaned) return profile

  const lines = cleaned.split('\n').map((l) => l.trim()).filter(Boolean)
  const unparsed = []

  for (const line of lines) {
    const ageMatch = line.match(/^(?:年龄段|年龄层|目标人群|人群)[：:]\s*(.+)$/i)
    if (ageMatch) {
      profile.ageRange = ageMatch[1].trim()
      continue
    }
    const prefMatch = line.match(/^(?:观影偏好|偏好标签|内容偏好|偏好)[：:]\s*(.+)$/i)
    if (prefMatch) {
      profile.preferences = splitPreferences(prefMatch[1])
      continue
    }
    const moodMatch = line.match(/^(?:情绪诉求|观看动机|补充|画像)[：:]\s*(.+)$/i)
    if (moodMatch) {
      profile.note = [profile.note, moodMatch[1].trim()].filter(Boolean).join('；')
      continue
    }
    unparsed.push(line)
  }

  if (!profile.ageRange && !profile.preferences.length && !profile.note && unparsed.length) {
    profile.note = unparsed.join(' ')
  }

  return applyAudienceTagMatching(profile)
}

export function serializeAudienceProfile(profile) {
  const p = profile || EMPTY_PROFILE
  const parts = []
  if (p.ageRange?.trim()) parts.push(`年龄段：${p.ageRange.trim()}`)
  if (p.preferences?.length) parts.push(`偏好：${p.preferences.join('、')}`)
  if (p.note?.trim()) parts.push(p.note.trim())
  return parts.join('\n')
}

export function normalizeAudienceProfile(profile, fallbackText = '') {
  const base =
    profile?.ageRange || profile?.preferences?.length || profile?.note
      ? {
          ageRange: profile.ageRange || '',
          preferences: [...(profile.preferences || [])],
          note: profile.note || '',
        }
      : fallbackText?.trim()
        ? parseAudienceProfile(fallbackText)
        : { ...EMPTY_PROFILE, preferences: [] }
  return applyAudienceTagMatching(base)
}

export function togglePreference(preferences, tag) {
  const set = new Set(preferences || [])
  if (set.has(tag)) set.delete(tag)
  else set.add(tag)
  return [...set]
}
