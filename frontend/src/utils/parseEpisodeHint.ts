const EPISODE_TEXT_RE = /第\s*(\d+)\s*集/

function coercePositiveInt(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value) && value >= 1) {
    return Math.floor(value)
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value.trim())
    if (Number.isFinite(parsed) && parsed >= 1) {
      return Math.floor(parsed)
    }
  }
  return null
}

/** 从对象字段或「第 N 集」文案解析集号。 */
export function parseEpisodeNumber(source: unknown): number | null {
  if (source == null) return null

  if (typeof source === 'number') {
    return coercePositiveInt(source)
  }

  if (typeof source === 'object' && !Array.isArray(source)) {
    const row = source as Record<string, unknown>
    const fromEpisodeNumber = coercePositiveInt(row.episode_number)
    if (fromEpisodeNumber != null) return fromEpisodeNumber
    const fromEpisode = coercePositiveInt(row.episode)
    if (fromEpisode != null) return fromEpisode
  }

  const text = typeof source === 'string' ? source.trim() : ''
  if (!text) return null

  const match = EPISODE_TEXT_RE.exec(text)
  if (match) {
    const parsed = Number(match[1])
    return Number.isFinite(parsed) && parsed >= 1 ? Math.floor(parsed) : null
  }

  return coercePositiveInt(text)
}
