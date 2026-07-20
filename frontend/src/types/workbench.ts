/** Runtime workbench-form contract types (from GET /api/v1/drama/meta/workbench-form/). */

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

export type ModuleCatalogItem = {
  id: string
  label_zh: string
  domain: string
  kind: 'core' | 'extension' | string
  lifecycle: string
  target_roles: string[]
  workbench_visible: boolean
  enable_when?: string
}

export type StageDefinition = {
  id: string
  orchestration_phase?: string
  stage_kind: 'main' | 'quality_loop' | 'optional' | string
  role: string
  role_label?: string
  /** Filled by backend from artifacts contract */
  artifact: string
  /** Chinese label merged from artifacts contract by backend */
  label_zh: string
  approval_required?: boolean
  batch_field?: string
  parallel_group?: string
  conditional?: boolean
  optional?: boolean
  visible_when?: string
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

export type ModulePanelConfig = {
  source?: string
  group_by?: string
  filter?: string
  evaluate_enable_when?: boolean
  allow_project_toggle?: boolean
}

/** Raw API payload shape (workbench-form.v1 + runtime enrichments). */
export type WorkbenchFormApiResponse = {
  schema_version?: string
  version?: string
  /** Skills bundle version — used as React Query cache partition key */
  skills_bundle_version?: string
  bundle_version?: string
  project_schema?: string
  parameters_contract?: string
  project_settings: {
    groups: Record<string, { label_zh: string; fields: string[] }> | SettingsGroupDef[]
    fields: Record<string, Omit<SettingsFieldDef, 'key' | 'label_zh'> & {
      label_zh?: string
      label?: string
      persist_path: string
      type: SettingsFieldType
    }>
  }
  stages: Array<
    Omit<StageDefinition, 'artifact' | 'label_zh'> & {
      artifact?: string
      label_zh?: string
      role_label?: string
      label?: string
    }
  >
  module_catalog: Record<string, Omit<ModuleCatalogItem, 'id'>> | ModuleCatalogItem[]
  module_panel?: ModulePanelConfig
  admin_settings?: {
    sections?: AdminSectionDef[]
    require_audit_reason?: boolean
    allow_git_ssot_override?: boolean
    policy?: string
  }
  theme_matrix?: ThemeMatrix
  derived_fields?: string[]
  system_fields?: string[]
  runtime_projection?: Record<string, unknown>
  navigation?: Record<string, unknown>
  external_tools?: Record<string, unknown>
}

/** Normalized definition consumed by UI (no static business fallbacks). */
export type WorkbenchDefinition = {
  schema_version: string
  skills_bundle_version: string
  groups: SettingsGroupDef[]
  fields: Record<string, SettingsFieldDef>
  stages: StageDefinition[]
  modules: ModuleCatalogItem[]
  module_panel?: ModulePanelConfig
  admin_sections: AdminSectionDef[]
  theme_matrix: ThemeMatrix | null
  delivery_tab_items: Array<{ id: string; label: string }>
}
