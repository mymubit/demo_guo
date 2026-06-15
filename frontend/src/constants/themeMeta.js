/** 题材展示元数据（C 端 fallback；Creation 以 catalog 为准并 merge） */
export const THEME_META_LIST = [
  { key: 'family-revenge', name: '家庭伦理复仇', color: '#e53e3e', emoji: '⚔️' },
  { key: 'overbearing-ceo', name: '豪门霸总', color: '#d69e2e', emoji: '💎' },
  { key: 'sweet-pet', name: '甜宠虐恋', color: '#d53f8c', emoji: '💕' },
  { key: 'time-travel', name: '穿越重生', color: '#805ad5', emoji: '⏰' },
  { key: 'urban-rebirth', name: '都市逆袭', color: '#3182ce', emoji: '🏙️' },
  { key: 'ancient-costume', name: '古装权谋', color: '#2f855a', emoji: '⚜️' },
  { key: 'suspense-reversal', name: '悬疑反转', color: '#5a67d8', emoji: '🕵️' },
  { key: 'healing', name: '情感疗愈', color: '#38a169', emoji: '🌱' },
  { key: 'mixed-theme', name: '混合题材', color: '#dd6b20', emoji: '🎭' },
]

const THEME_BY_KEY = Object.fromEntries(THEME_META_LIST.map((t) => [t.key, t]))

const DEFAULT_THEME = THEME_BY_KEY['mixed-theme']

export function getThemeMeta(key) {
  if (!key) return { ...DEFAULT_THEME, key: 'mixed-theme' }
  return THEME_BY_KEY[key] || { ...DEFAULT_THEME, key, name: key }
}

/** 将 fusion catalog 条目与本地 fallback 合并 */
export function mergeThemeWithCatalog(item) {
  if (!item || typeof item !== 'object') return DEFAULT_THEME
  const fallback = getThemeMeta(item.key)
  return {
    key: item.key || fallback.key,
    name: item.displayName || item.name || fallback.name,
    color: item.color || fallback.color,
    emoji: item.icon || item.emoji || fallback.emoji,
  }
}
