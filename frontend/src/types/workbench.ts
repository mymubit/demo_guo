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
  options: AxisOption[]
}

export type FlavorTagOption = {
  value: string
  label_zh: string
  category: string
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
  emotion: string
  identity: string
  conflict: string
  world: string
  flavor_tags?: string[]
}

export type ThemeMatrix = {
  version?: string
  dim_order: Array<'emotion' | 'identity' | 'conflict' | 'world'>
  axes: Record<string, AxisConfig>
  flavor_tags: {
    max_select: number
    hint?: string
    categories: FlavorCategory[]
    options: FlavorTagOption[]
  }
  featured_combos?: FeaturedCombo[]
  preset_templates?: Array<{ code: string; label_zh: string }>
}

export type ModuleCatalogItem = {
  id: string
  label_zh: string
  domain: string
  kind: 'core' | 'extension'
  lifecycle: string
  target_roles: string[]
  workbench_visible: boolean
  enable_when?: string
}

export type StageDefinition = {
  id: string
  orchestration_phase?: string
  stage_kind: 'main' | 'quality_loop' | 'optional'
  role: string
  artifact: string
  approval_required?: boolean
  batch_field?: string
  parallel_group?: string
  conditional?: boolean
  optional?: boolean
  visible_when?: string
  label_zh: string
}

export type SettingsFieldType = 'string' | 'integer' | 'boolean' | 'array' | 'object'

export type SettingsFieldDef = {
  key: string
  type: SettingsFieldType
  persist_path: string
  label_zh: string
  ui_widget?: 'textarea' | 'select' | 'number' | 'switch' | 'tags' | 'matrix' | 'checklist'
  enum?: string[]
  enum_items?: string[]
  default?: unknown
  minimum?: number
  maximum?: number
  required?: boolean
  required_when?: string
  visible_when?: string
  options?: Array<{ value: string; label: string }>
}

export type SettingsGroupDef = {
  id: string
  label_zh: string
  fields: string[]
}
