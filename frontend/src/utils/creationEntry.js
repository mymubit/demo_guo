const DEFAULT_SHOW = {
  theme: true,
  coreIdea: true,
  outline: false,
  novel: false,
  referenceBlock: 'hidden',
  ipSequel: false,
  projectParams: true,
  audience: true,
}

function emptyPipelineHints() {
  return { prefilledSteps: [], caption: '' }
}

function mergePipelineHints(configured = {}) {
  const cfg = configured && typeof configured === 'object' ? configured : {}
  return {
    prefilledSteps: Array.isArray(cfg.prefilledSteps) ? cfg.prefilledSteps : [],
    caption: cfg.caption || '',
  }
}

import { composeCoreIdea, validateStoryBrief } from './storyBrief'
import { serializeAudienceProfile } from './audienceProfile'

function mergeEntryValidation(configured = {}) {
  const cfg = configured && typeof configured === 'object' ? configured : {}
  const cfgRequired =
    cfg.requiredFields && typeof cfg.requiredFields === 'object' ? cfg.requiredFields : {}
  return {
    ...cfg,
    requiredFields: { ...cfgRequired },
  }
}

const FORM_FIELD_ACCESSORS = {
  reference_work: (formData) => formData.referenceWork,
  outline_text: (formData) => formData.outline,
  novel_text: (formData) => formData.novelText,
  ip_keep_rules: (formData) => formData.ipKeepRules,
  theme: (formData) => formData.theme,
  core_idea: (formData) => composeCoreIdea(formData),
  audience: (formData) =>
    serializeAudienceProfile(formData.audienceProfile) || (formData.audience || '').trim(),
}

function getRequiredFieldRules(profile) {
  const requiredFields = profile?.validation?.requiredFields
  return requiredFields && typeof requiredFields === 'object' ? requiredFields : {}
}

export function getRequiredFieldMinLength(profile, field, fallback = 1) {
  const rule = getRequiredFieldRules(profile)[field]
  return Number(rule?.minLength || fallback)
}

function formValueForRule(formData, field) {
  const getter = FORM_FIELD_ACCESSORS[field]
  return String(getter ? getter(formData) ?? '' : formData[field] ?? '')
}

/** 从 fusion catalog 解析入口 profile（SSOT：后端 creationEntryProfiles） */
export function resolveEntryProfile(catalog, entryKey) {
  const key = entryKey || 'from-scratch'
  const profiles = catalog?.creationEntryProfiles || {}
  const catalogProfile =
    (profiles[key] && typeof profiles[key] === 'object' ? profiles[key] : null) ||
    (profiles['from-scratch'] && typeof profiles['from-scratch'] === 'object'
      ? profiles['from-scratch']
      : {})
  const catalogShow =
    catalogProfile?.show && typeof catalogProfile.show === 'object' ? catalogProfile.show : {}

  return {
    ...catalogProfile,
    pipelineHints: mergePipelineHints(catalogProfile?.pipelineHints || catalogProfile?.pipeline),
    validation: mergeEntryValidation(catalogProfile?.validation),
    show: {
      ...DEFAULT_SHOW,
      ...catalogShow,
    },
  }
}

export function getEntryPipelineHints(entryKey, profile = null, catalog = null) {
  if (profile?.pipelineHints && typeof profile.pipelineHints === 'object') {
    return profile.pipelineHints
  }
  if (catalog) {
    return resolveEntryProfile(catalog, entryKey).pipelineHints
  }
  return emptyPipelineHints()
}

/** 创意输入阶段当前子步骤（0-based，不含「技能流水线」） */
export function getEntryFormStepIndex(formData, profile, stepCount = 4) {
  const show = profile?.show || DEFAULT_SHOW
  const confirmStepIndex = Math.max(0, stepCount - 2)

  const requiredRules = getRequiredFieldRules(profile)
  if (
    Object.entries(requiredRules).some(([field, rule]) => {
      const minLength = Number(rule?.minLength || 1)
      return formValueForRule(formData, field).trim().length < minLength
    })
  ) {
    return 0
  }
  if (show.theme !== false && !formData.theme) return 0

  if (show.coreIdea && !validateStoryBrief(formData).ok) return Math.min(1, confirmStepIndex)

  if (validateEntryForm(formData, profile).ok) return confirmStepIndex

  return Math.min(1, confirmStepIndex)
}

export function getEntryFormChips(show = {}) {
  const chips = []
  if (show.novel) chips.push('小说原文')
  if (show.outline) chips.push('分集大纲')
  if (show.ipSequel) chips.push('IP 约束')
  if (show.theme !== false) chips.push('题材')
  if (show.projectParams !== false) chips.push('项目参数')
  if (show.audience) chips.push('目标受众')
  if (show.coreIdea) chips.push('故事策划')
  return chips
}

export function validateEntryForm(formData, profile) {
  const show = profile?.show || DEFAULT_SHOW
  if (show.theme && !formData.theme) {
    return { ok: false, message: '请先选择题材' }
  }
  if (show.coreIdea) {
    const briefCheck = validateStoryBrief(formData)
    if (!briefCheck.ok) return briefCheck
  }
  const requiredRules = getRequiredFieldRules(profile)
  for (const [field, rule] of Object.entries(requiredRules)) {
    const minLength = Number(rule?.minLength || 1)
    const label = rule?.label || field
    if (formValueForRule(formData, field).trim().length < minLength) {
      return { ok: false, message: `请填写${label}（至少 ${minLength} 字）` }
    }
  }
  return { ok: true, message: '生成项目简报，开始创作' }
}

export function buildSubmitPayload(formData, pipelineMode, profile = null) {
  const entry = formData.creationEntry || 'from-scratch'
  let coreIdea = composeCoreIdea(formData)
  const show = profile?.show || {}
  if (!show.coreIdea && (formData.outline || '').trim()) {
    coreIdea = (formData.outline || '').trim().slice(0, 500) || '基于已有大纲改编'
  } else if (!show.coreIdea && (formData.novelText || '').trim()) {
    coreIdea = (formData.novelText || '').trim().slice(0, 200) || '小说改编项目'
  }

  const payload = {
    theme: formData.theme,
    core_idea: coreIdea,
    episode_count: formData.episodes,
    format_variant: formData.format,
    audience:
      serializeAudienceProfile(formData.audienceProfile) || (formData.audience || '').trim(),
    reference_work: (formData.referenceWork || '').trim(),
    target_platform: formData.targetPlatform,
    budget_level: formData.budgetLevel,
    episode_duration_minutes: formData.episodeDuration ?? 2,
    creation_entry: entry,
    pipeline_mode: pipelineMode,
  }

  if ((formData.outline || '').trim()) payload.outline_text = formData.outline.trim()
  if ((formData.novelText || '').trim()) payload.novel_text = formData.novelText.trim()
  if (formData.ipSequelMode) payload.ip_sequel_mode = formData.ipSequelMode
  if ((formData.ipKeepRules || '').trim()) payload.ip_keep_rules = formData.ipKeepRules.trim()
  if (formData.pipelinePackId) payload.pipeline_pack_id = formData.pipelinePackId

  return payload
}

export { DEFAULT_SHOW }
