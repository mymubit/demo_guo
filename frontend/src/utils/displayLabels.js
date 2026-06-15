/** C 端展示：英文 code / slug → 中文标签，避免 raw code 露出 */

export function containsChinese(text) {
  return /[\u4e00-\u9fff]/.test(String(text || ''))
}

export function isEnglishSlug(text) {
  const s = String(text || '').trim()
  if (!s || containsChinese(s)) return false
  return /^[a-z0-9]+(?:[-_/][a-z0-9]+)*$/i.test(s)
}

export function resolveFromMap(code, map = {}, { allowChinese = true, fallback = '' } = {}) {
  const raw = String(code || '').trim()
  if (!raw) return fallback
  if (map[raw]) return map[raw]
  if (allowChinese && containsChinese(raw)) return raw
  return fallback
}

export const ROLE_LABELS = {
  'protagonist-female': '女主',
  'protagonist-male': '男主',
  protagonist: '主角',
  'antagonist-female': '女反派',
  'antagonist-male': '男反派',
  antagonist: '反派',
  supporting: '配角',
  cameo: '客串',
}

export function resolveRoleTypeLabel(char = {}) {
  const role = char.roleType || ''
  const label = char.roleTypeLabel || ''
  if (label && label !== role && !isEnglishSlug(label)) return label
  if (ROLE_LABELS[role]) return ROLE_LABELS[role]
  if (role.startsWith('antagonist')) {
    if (char.gender === 'male') return '男反派'
    if (char.gender === 'female') return '女反派'
    return '反派'
  }
  if (role.startsWith('protagonist')) {
    if (char.gender === 'female') return '女主'
    if (char.gender === 'male') return '男主'
    return '主角'
  }
  if (label && !isEnglishSlug(label)) return label
  return ROLE_LABELS[role] || (containsChinese(role) ? role : '')
}

export const RELATION_LABELS = {
  'parent-child': '亲子',
  spouse: '夫妻',
  sibling: '兄弟姐妹',
  'romantic-lover': '恋人',
  enemy: '敌对',
  'friend-confidant': '挚友',
  'mentor-protege': '师徒',
  colleague: '同事',
  'ex-lover': '前任',
  'business-partner': '商业伙伴',
  'secret-identity': '隐藏身份',
  other: '其他',
}

export function resolveRelationTypeLabel(rel = {}) {
  const type = rel.relationType || ''
  const label = rel.relationTypeLabel || ''
  if (label && label !== type && !isEnglishSlug(label)) return label
  return resolveFromMap(type, RELATION_LABELS, { fallback: containsChinese(type) ? type : '' })
}

export const THEME_LABELS = {
  'family-revenge': '家庭伦理复仇',
  'overbearing-ceo': '豪门霸总',
  'sweet-pet': '甜宠虐恋',
  'time-travel': '穿越重生',
  'urban-rebirth': '都市逆袭',
  'ancient-costume': '古装权谋',
  'suspense-reversal': '悬疑反转',
  'male-advancement': '都市男频',
  'mixed-theme': '混合题材',
  'urban-romance': '都市情感',
}

export function resolveThemeCodeLabel(code, label) {
  const explicit = String(label || '').trim()
  if (explicit && explicit !== code && !isEnglishSlug(explicit)) return explicit
  return resolveFromMap(code, THEME_LABELS)
}

export const FORMAT_LABELS = {
  'variant-a': '变体 A',
  'variant-b': '变体 B',
  'variant-c': '变体 C',
  'variant-d': '变体 D',
}

export function resolveFormatVariantLabel(code, label) {
  const explicit = String(label || '').trim()
  if (explicit && explicit !== code && !isEnglishSlug(explicit)) return explicit
  return resolveFromMap(code, FORMAT_LABELS)
}

export const LOCATION_LABELS = {
  urban: '都市',
  rural: '乡村',
  ancient: '古装',
  fantasy: '幻想',
  mixed: '混合',
}

export function resolveLocationTypeLabel(code, label) {
  const explicit = String(label || '').trim()
  if (explicit && explicit !== code && !isEnglishSlug(explicit)) return explicit
  return resolveFromMap(code, LOCATION_LABELS)
}

export function resolveArchetypeLabel(char = {}, bible = {}) {
  const code = (char.archetypeCode || '').trim()
  const label = (char.archetypeLabel || '').trim()
  if (label && label !== code && !isEnglishSlug(label)) return label
  const hit = bible?.archetypeIndex?.[code]
  return hit ? String(hit).trim() : ''
}

export function resolveHookLabel(ep = {}) {
  const label = String(ep.hookTypeLabel || '').trim()
  const code = String(ep.hookTypeCode || '').trim()
  if (label && label !== code) return label
  return containsChinese(code) ? code : ''
}

export function resolveReversalLabel(ep = {}) {
  const label = String(ep.reversalPatternLabel || '').trim()
  const code = String(ep.reversalCode || ep.reversalPatternCode || '').trim()
  if (label && label !== code) return label
  return containsChinese(code) ? code : ''
}
