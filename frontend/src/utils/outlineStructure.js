/** 六阶段结构展陈判定（PlotArchitectOutput / 按钮显隐共用） */

export const STAGE_LABELS = {
  opening: '开篇',
  warming: '升温',
  climax: '高潮',
  turning: '转折',
  sprint: '冲刺',
  ending: '结局',
}

export const STAGE_ORDER = ['opening', 'warming', 'climax', 'turning', 'sprint', 'ending']

const STAGE_KEY_ALIASES = {
  opening: 'opening',
  open: 'opening',
  开篇: 'opening',
  warming: 'warming',
  warming_up: 'warming',
  warm_up: 'warming',
  升温: 'warming',
  climax: 'climax',
  高潮: 'climax',
  turning: 'turning',
  turning_point: 'turning',
  转折: 'turning',
  sprint: 'sprint',
  冲刺: 'sprint',
  ending: 'ending',
  end: 'ending',
  结局: 'ending',
}

export function extractStageSummary(val) {
  if (!val || typeof val !== 'object') return ''
  for (const key of [
    'core_direction',
    'core_design',
    'core_task',
    'stage_goal',
    'summary',
    'stage_name',
  ]) {
    const text = String(val[key] || '').trim()
    if (text) return text
  }
  const points = val.key_plot_points || val.highlights
  if (Array.isArray(points) && points.length) {
    return points.slice(0, 3).map(String).join('；')
  }
  return ''
}

export function normalizeSixStage(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return []
  const byKey = {}
  Object.entries(raw).forEach(([key, val]) => {
    const canon = STAGE_KEY_ALIASES[String(key).toLowerCase()] || STAGE_KEY_ALIASES[key] || key
    if (!val || typeof val !== 'object') return
    const prev = byKey[canon] || {}
    byKey[canon] = { ...prev, ...val }
  })
  return STAGE_ORDER.filter((key) => {
    const val = byKey[key]
    if (!val) return false
    return Boolean(extractStageSummary(val) || String(val.episode_range || val.episodes_range || '').trim())
  }).map((key, index) => ({
    key,
    index: index + 1,
    title: STAGE_LABELS[key] || key,
    subtitle: byKey[key]?.episode_range || byKey[key]?.episodes_range || '',
    summary: extractStageSummary(byKey[key]),
  }))
}

export function countDisplayableOutlineStages(rawArtifact, outputView) {
  const viewBlock = (outputView?.blocks || []).find((b) => b.type === 'series_outline')
  const viewStages = viewBlock?.stages || []
  if (Array.isArray(viewStages) && viewStages.length > 0) {
    return viewStages.filter((s) => extractStageSummary(s) || s?.subtitle || s?.summary).length
  }
  const fromStruct = normalizeSixStage(rawArtifact?.six_stage_structure)
  if (fromStruct.length) return fromStruct.length
  const narrative = rawArtifact?.six_stage_narrative
  if (Array.isArray(narrative) && narrative.length) {
    return narrative.filter((item) => extractStageSummary(item)).length
  }
  return 0
}
