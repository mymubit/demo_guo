export const LAYER_OPTIONS = [
  { value: '', label: '全部层级' },
  { value: 'foundation', label: '基础能力层' },
  { value: 'business', label: '业务技能层' },
  { value: 'tool', label: '工具能力层' },
]

export const LAYER_LABEL = {
  foundation: '基础能力层',
  business: '业务技能层',
  tool: '工具能力层',
}

export const STATUS_FILTER_TABS = [
  { value: '', label: '全部' },
  { value: 'draft', label: '草稿' },
  { value: 'active', label: '上线' },
  { value: 'gray', label: '灰度' },
  { value: 'deprecated', label: '废弃' },
]

export const SKILL_DETAIL_TABS = [
  { key: 'overview', label: '概览' },
  { key: 'prompt', label: 'Prompt' },
  { key: 'schema', label: 'Schema' },
  { key: 'versions', label: '版本' },
  { key: 'stats', label: '统计' },
  { key: 'evolution', label: '进化' },
  { key: 'rules', label: '规则库' },
]

export const EMPTY_SKILL_FORM = {
  skill_id: '',
  name: '',
  version: '1.0.0',
  skill_layer: '',
  sub_category: '',
  system_hint: '',
  content: '',
  input_schema: '{}',
  output_schema: '{}',
  timeout_seconds: 60,
  quota_cost: 0,
  fallback_skill_id: '',
  retry_policy: '{"max_attempts": 2, "backoff_seconds": 5}',
}

export function formatJsonField(value, fallback = {}) {
  if (value == null || value === '') return JSON.stringify(fallback, null, 2)
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return JSON.stringify(fallback, null, 2)
  }
}

export function mapSkillToForm(skill) {
  if (!skill) return { ...EMPTY_SKILL_FORM }
  return {
    skill_id: skill.skill_id || '',
    name: skill.name || '',
    version: skill.version || '1.0.0',
    skill_layer: skill.skill_layer || '',
    sub_category: skill.sub_category || '',
    system_hint: skill.system_hint || '',
    content: skill.content || '',
    input_schema: formatJsonField(skill.input_schema, {}),
    output_schema: formatJsonField(skill.output_schema, {}),
    timeout_seconds: skill.timeout_seconds ?? 60,
    quota_cost: skill.quota_cost ?? 0,
    fallback_skill_id: skill.fallback_skill_id || '',
    retry_policy: formatJsonField(skill.retry_policy, { max_attempts: 2, backoff_seconds: 5 }),
  }
}

export function buildSkillPayload(form) {
  return {
    ...form,
    input_schema: JSON.parse(form.input_schema || '{}'),
    output_schema: JSON.parse(form.output_schema || '{}'),
    retry_policy: JSON.parse(form.retry_policy || '{}'),
    timeout_seconds: Number(form.timeout_seconds),
    quota_cost: Number(form.quota_cost),
  }
}
