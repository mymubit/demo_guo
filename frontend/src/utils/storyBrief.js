/** 故事策划字段 — 与 AI 灵感策划输出对齐 */

import { serializeAudienceProfile } from './audienceProfile'

export const EMOTIONAL_TONE_PRESETS = [
  '甜虐交织',
  '逆袭爽感',
  '悬疑反转',
  '虐恋重生',
  '豪门恩怨',
  '都市情感',
  '复仇打脸',
  '温情治愈',
]

const FIELD_SPECS = [
  { key: 'idea', labels: ['一句话梗概', '一句话创意', '核心创意', '梗概'] },
  { key: 'coreConflict', labels: ['核心冲突'] },
  { key: 'emotionalTone', labels: ['情绪基调'] },
  { key: 'openingHooks', labels: ['前三集钩子', '前三集', '开篇钩子'] },
]

/** 解析灵感策划 AI 返回的纯文本 */
export function parseInspirationPlan(text) {
  const result = { idea: '', coreConflict: '', emotionalTone: '', openingHooks: '' }
  if (!text?.trim()) return result

  const normalized = String(text)
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\r\n/g, '\n')

  let currentKey = null
  let inPreamble = true
  const buffers = { idea: [], coreConflict: [], emotionalTone: [], openingHooks: [] }

  for (const rawLine of normalized.split('\n')) {
    const line = rawLine.trim()
    if (!line) {
      if (inPreamble && buffers.idea.length) buffers.idea.push('')
      else if (currentKey) buffers[currentKey].push('')
      continue
    }

    let matchedKey = null
    let inlineValue = ''

    for (const spec of FIELD_SPECS) {
      for (const label of spec.labels) {
        const colonMatch = line.match(new RegExp(`^${label}\\s*[：:]\\s*(.*)$`))
        if (colonMatch) {
          matchedKey = spec.key
          inlineValue = colonMatch[1] || ''
          break
        }
        if (line === label) {
          matchedKey = spec.key
          break
        }
      }
      if (matchedKey) break
    }

    if (matchedKey) {
      inPreamble = false
      currentKey = matchedKey
      if (inlineValue) buffers[matchedKey].push(inlineValue)
      continue
    }

    if (inPreamble) {
      buffers.idea.push(rawLine.trimEnd())
      continue
    }

    if (currentKey) buffers[currentKey].push(rawLine.trimEnd())
  }

  for (const spec of FIELD_SPECS) {
    result[spec.key] = buffers[spec.key].join('\n').trim()
  }

  if (!result.idea && !result.coreConflict && !result.emotionalTone && !result.openingHooks) {
    result.idea = normalized.trim().slice(0, 500)
  }

  return result
}

/** 提交给后端的 core_idea：结构化字段合并为一段 */
export function composeCoreIdea(formData) {
  const hook = (formData.idea || '').trim()
  const conflict = (formData.coreConflict || '').trim()
  const tone = (formData.emotionalTone || '').trim()
  const hooks = (formData.openingHooks || '').trim()

  if (!conflict && !tone && !hooks) return hook

  const parts = []
  if (hook) parts.push(hook)
  if (conflict) parts.push(`核心冲突：${conflict}`)
  if (tone) parts.push(`情绪基调：${tone}`)
  if (hooks) parts.push(`前三集钩子：${hooks}`)
  return parts.join('\n\n')
}

export function storyBriefContext(formData) {
  return {
    theme: formData.theme,
    episode_count: formData.episodes,
    core_idea: composeCoreIdea(formData),
    idea: formData.idea,
    core_conflict: formData.coreConflict,
    emotional_tone: formData.emotionalTone,
    opening_hooks: formData.openingHooks,
    audience:
      serializeAudienceProfile(formData.audienceProfile) || formData.audience || '',
  }
}

export function validateStoryBrief(formData) {
  const hook = (formData.idea || '').trim()
  const conflict = (formData.coreConflict || '').trim()
  const tone = (formData.emotionalTone || '').trim()

  if (hook.length >= 10) return { ok: true }
  if (conflict.length >= 10 && tone.length >= 2) return { ok: true }
  return {
    ok: false,
    message: '请填写一句话梗概（≥10 字），或填写核心冲突与情绪基调',
  }
}
