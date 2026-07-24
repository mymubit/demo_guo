import type { AdminSectionDef, SettingsFieldDef, SettingsFieldType, SettingsGroupDef, ThemeMatrix } from '@/types/workbench'

export type ProjectFormApiResponse = {
  schema_version: 'v6-project-form.v1'
  skills_version: string
  groups: Record<string, { label_zh: string; fields: string[] }> | SettingsGroupDef[]
  fields: Record<string, Omit<SettingsFieldDef, 'key' | 'label_zh'> & {
    label_zh?: string
    label?: string
    description_zh?: string
    purpose_zh?: string
    persist_path: string
    type: SettingsFieldType
  }>
  theme_matrix: ThemeMatrix
  policy_sections: AdminSectionDef[]
}

export type ProjectFormDefinition = {
  schema_version: 'v6-project-form.v1'
  skills_version: string
  groups: SettingsGroupDef[]
  fields: Record<string, SettingsFieldDef>
  theme_matrix: ThemeMatrix
  policy_sections: AdminSectionDef[]
  delivery_items: Array<{ id: string; label: string }>
}
