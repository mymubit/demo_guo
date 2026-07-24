import { resolveUiWidget } from '@/config/workbench'
import type { SettingsFieldDef, SettingsGroupDef } from '@/types/workbench'
import type { ProjectFormApiResponse, ProjectFormDefinition } from '@/types/projectForm'

function normalizeField(key: string, raw: ProjectFormApiResponse['fields'][string]): SettingsFieldDef {
  const items = raw.items_enum ?? raw.enum_items
  const options = raw.options?.map((option) => ({ ...option, label: option.label_zh || option.label || option.value }))
    ?? raw.enum?.map((value) => ({ value, label: value }))
    ?? items?.map((value) => ({ value, label: value }))
  return {
    ...raw,
    key,
    label_zh: raw.label_zh || raw.label || key,
    ui_widget: resolveUiWidget({ ...raw, items_enum: items }),
    items_enum: items,
    options,
  }
}

function normalizeGroups(groups: ProjectFormApiResponse['groups']): SettingsGroupDef[] {
  if (Array.isArray(groups)) return groups.map((group) => ({ ...group, fields: [...group.fields] }))
  return Object.entries(groups).map(([id, group]) => ({ id, label_zh: group.label_zh, fields: [...group.fields] }))
}

export function normalizeProjectForm(raw: ProjectFormApiResponse): ProjectFormDefinition {
  if (raw.schema_version !== 'v6-project-form.v1') throw new Error(`不支持的项目表单契约：${raw.schema_version}`)
  if (!raw.skills_version || !raw.fields || !raw.groups || !raw.theme_matrix) throw new Error('V6 项目表单契约不完整')
  const fields = Object.fromEntries(Object.entries(raw.fields).map(([key, field]) => [key, normalizeField(key, field)]))
  const delivery = fields.deliverables
  return {
    schema_version: raw.schema_version,
    skills_version: raw.skills_version,
    groups: normalizeGroups(raw.groups),
    fields,
    theme_matrix: raw.theme_matrix,
    policy_sections: raw.policy_sections ?? [],
    delivery_items: delivery?.options?.map((item) => ({ id: item.value, label: item.label })) ?? [],
  }
}

export function projectFormQueryKey(skillsVersion?: string) {
  return skillsVersion ? ['meta', 'project-form', skillsVersion] as const : ['meta', 'project-form'] as const
}
