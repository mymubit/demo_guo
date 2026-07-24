/** Shared V6 project-field and operation execution types. */

export type FieldOption = {
  value: string
  label: string
  label_zh?: string
  desc?: string
  /** 市场热度分层：hot / standard / longtail */
  tier?: string
  /** 标签分类 id（theme-matrix categories） */
  category?: string
}

export type AxisOption = {
  value: string
  label_zh: string
  desc?: string
}

export type AxisConfig = {
  label_zh: string
  hint?: string
  min_select?: number
  max_select?: number
  required?: boolean
  options: AxisOption[]
}

export type FlavorTagOption = {
  value: string
  label_zh: string
  category: string
  tier?: string
}

export type FlavorCategory = {
  id: string
  label_zh: string
  tags: string[]
}

export type FeaturedCombo = {
  code: string
  label_zh?: string
  label?: string
  heat?: string
  /** preset=常用题材模板；featured=创新杂交组合 */
  kind?: 'preset' | 'featured'
  emotion: string
  identity: string
  conflict: string
  world: string
  flavor_tags?: string[]
  audience_channel?: string
  protagonist_structure?: string
}

/** Theme matrix view-model derived from resolved parameter fields (not a static copy). */
export type ThemeMatrix = {
  version?: string
  dim_order: string[]
  axes: Record<string, AxisConfig>
  flavor_tags: {
    max_select: number
    hint?: string
    categories: FlavorCategory[]
    options: FlavorTagOption[]
  }
  featured_combos?: FeaturedCombo[]
  /** 与 featured 同形：含四轴，供常用题材点选 */
  preset_templates?: FeaturedCombo[]
  /** 自定义四轴软引导（prefer/discourage） */
  axis_guidance?: {
    display_order?: string[]
    soft_rules?: Array<{
      when: Record<string, string>
      prefer?: Record<string, string[]>
      discourage?: Record<string, string[]>
      note?: string
    }>
  }
  audience_channel?: {
    label_zh: string
    hint?: string
    required?: boolean
    default?: string
    options: AxisOption[]
  }
  protagonist_structure?: {
    label_zh: string
    hint?: string
    required?: boolean
    options: AxisOption[]
  }
}

export type OperationInputField = {
  key: string
  label_zh: string
  description_zh?: string
  purpose_zh?: string
  widget: 'textarea' | 'text' | 'number' | 'episode_range' | 'checklist' | 'findings_checklist'
  placeholder?: string
  project_default?: string
  minimum?: number
  options?: Array<{ value: string; label_zh: string }>
}

export type V6Persona = {
  id: string
  version: number
  label_zh: string
  purpose: string
  responsibilities: string[]
  boundaries: string[]
  decision_protocol: string[]
  output_expectations: string[]
  anti_patterns?: string[]
}

export type V6AtomicRule = {
  id: string
  statement: string
  severity: 'hard' | 'soft' | 'advisory'
  category: string
}

export type V6Capability = {
  id: string
  label_zh: string
  version: number
  inputs: string[]
  outputs: string[]
  rules: string[]
  rule_definitions?: V6AtomicRule[]
}

export type SettingsFieldType = 'string' | 'integer' | 'boolean' | 'array' | 'object' | string

export type SettingsUiWidget =
  | 'textarea'
  | 'select'
  | 'number'
  | 'switch'
  | 'tags'
  | 'matrix'
  | 'checklist'
  | string

export type SettingsFieldDef = {
  key: string
  type: SettingsFieldType
  persist_path: string
  label_zh: string
  description_zh?: string
  purpose_zh?: string
  ui_widget?: SettingsUiWidget
  enum?: string[]
  enum_items?: string[]
  items_enum?: string[]
  default?: unknown
  minimum?: number
  maximum?: number
  max_items?: number
  required?: boolean
  required_when?: string
  visible_when?: string
  options?: FieldOption[]
  /** Nested object axes (e.g. genre_matrix) from parameter contract resolution */
  fields?: Record<
    string,
    {
      label?: string
      label_zh?: string
      required?: boolean
      options?: FieldOption[]
    }
  >
  items?: { type?: string }
  config_scope?: string
}

export type SettingsGroupDef = {
  id: string
  label_zh: string
  fields: string[]
}

export type AdminSectionDef = {
  id: string
  source: string
  label_zh?: string
}

