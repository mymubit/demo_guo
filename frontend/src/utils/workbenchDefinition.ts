import { resolveUiWidget } from '@/config/workbench'
import type {
  AdminSectionDef,
  ModuleCatalogItem,
  SettingsFieldDef,
  SettingsGroupDef,
  StageDefinition,
  ThemeMatrix,
  WorkbenchDefinition,
  WorkbenchFormApiResponse,
} from '@/types/workbench'

function optionLabel(opt: { value: string; label?: string; label_zh?: string }): string {
  return opt.label_zh || opt.label || opt.value
}

function fieldLabel(key: string, field: { label_zh?: string; label?: string }): string {
  return field.label_zh || field.label || key
}

function normalizeOptions(
  options: Array<{ value: string; label?: string; label_zh?: string }> | undefined,
  enumValues: string[] | undefined,
): Array<{ value: string; label: string }> | undefined {
  if (options && options.length > 0) {
    return options.map((o) => ({ value: o.value, label: optionLabel(o) }))
  }
  if (enumValues && enumValues.length > 0) {
    return enumValues.map((value) => ({ value, label: value }))
  }
  return undefined
}

export function normalizeSettingsField(
  key: string,
  raw: WorkbenchFormApiResponse['project_settings']['fields'][string],
): SettingsFieldDef {
  const itemsEnum = raw.items_enum ?? raw.enum_items
  const options = normalizeOptions(raw.options, raw.enum) ??
    (itemsEnum ? itemsEnum.map((value) => ({ value, label: value })) : undefined)

  return {
    key,
    type: raw.type,
    persist_path: raw.persist_path,
    label_zh: fieldLabel(key, raw),
    ui_widget: resolveUiWidget({ ...raw, items_enum: itemsEnum }),
    enum: raw.enum,
    enum_items: raw.enum_items,
    items_enum: itemsEnum,
    default: raw.default,
    minimum: raw.minimum,
    maximum: raw.maximum,
    max_items: raw.max_items,
    required: raw.required,
    required_when: raw.required_when,
    visible_when: raw.visible_when,
    options,
    fields: raw.fields,
    items: raw.items,
    config_scope: raw.config_scope,
  }
}

export function normalizeGroups(
  groups: WorkbenchFormApiResponse['project_settings']['groups'],
): SettingsGroupDef[] {
  if (Array.isArray(groups)) {
    return groups.map((g) => ({ id: g.id, label_zh: g.label_zh, fields: [...g.fields] }))
  }
  return Object.entries(groups).map(([id, group]) => ({
    id,
    label_zh: group.label_zh,
    fields: [...group.fields],
  }))
}

export function normalizeStages(
  stages: WorkbenchFormApiResponse['stages'],
): StageDefinition[] {
  return stages.map((stage) => {
    if (!stage.artifact) {
      throw new Error(`工作台阶段「${stage.id}」缺少 artifact（后端应合并产物契约）`)
    }
    const label_zh = stage.label_zh || stage.label
    if (!label_zh) {
      throw new Error(`工作台阶段「${stage.id}」缺少 label_zh（后端应合并产物中文标签）`)
    }
    if (!stage.role_label) {
      throw new Error(`工作台阶段「${stage.id}」缺少 role_label`)
    }
    return {
      id: stage.id,
      orchestration_phase: stage.orchestration_phase,
      stage_kind: stage.stage_kind,
      role: stage.role,
      role_label: stage.role_label,
      artifact: stage.artifact,
      label_zh,
      approval_required: stage.approval_required,
      batch_field: stage.batch_field,
      parallel_group: stage.parallel_group,
      conditional: stage.conditional,
      optional: stage.optional,
      visible_when: stage.visible_when,
    }
  })
}

export function normalizeModules(
  catalog: WorkbenchFormApiResponse['module_catalog'],
): ModuleCatalogItem[] {
  if (Array.isArray(catalog)) {
    return catalog.map((m) => ({ ...m }))
  }
  return Object.entries(catalog).map(([id, item]) => ({
    id,
    label_zh: item.label_zh,
    domain: item.domain,
    kind: item.kind,
    lifecycle: item.lifecycle,
    target_roles: [...item.target_roles],
    workbench_visible: item.workbench_visible,
    enable_when: item.enable_when,
  }))
}

export function buildThemeMatrixFromFields(
  fields: Record<string, SettingsFieldDef>,
  embedded?: ThemeMatrix | null,
): ThemeMatrix | null {
  if (embedded) return embedded

  const genre = fields.genre_matrix
  const flavor = fields.flavor_tags
  const preset = fields.preset_theme_code
  if (!genre?.fields) return null

  const dimOrder = Object.keys(genre.fields)
  const axes: ThemeMatrix['axes'] = {}
  for (const [axisKey, axis] of Object.entries(genre.fields)) {
    axes[axisKey] = {
      label_zh: axis.label_zh || axis.label || axisKey,
      required: axis.required,
      options: (axis.options ?? []).map((o) => ({
        value: o.value,
        label_zh: o.label_zh || o.label || o.value,
        desc: (o as { desc?: string }).desc,
      })),
    }
  }

  const flavorOptions = (flavor?.options ?? []).map((o) => ({
    value: o.value,
    label_zh: o.label_zh || o.label || o.value,
    category: o.category ?? 'all',
    tier: o.tier,
  }))

  // 按后端透传的 category 元数据分组；无分组信息时退化为单组
  const categoryIds = [...new Set(flavorOptions.map((o) => o.category))]
  const categories =
    flavorOptions.length === 0
      ? []
      : categoryIds.map((id) => ({
          id,
          label_zh: id === 'all' ? '全部' : id,
          tags: flavorOptions.filter((o) => o.category === id).map((o) => o.value),
        }))

  return {
    dim_order: dimOrder,
    axes,
    flavor_tags: {
      max_select: flavor?.max_items ?? 5,
      categories,
      options: flavorOptions,
    },
    preset_templates: (preset?.options ?? []).map((o) => ({
      code: o.value,
      label_zh: o.label_zh || o.label || o.value,
    })),
    featured_combos: embedded?.featured_combos ?? [],
  }
}

export function deliveryTabsFromFields(
  fields: Record<string, SettingsFieldDef>,
): Array<{ id: string; label: string }> {
  const delivery = fields.delivery_items
  if (!delivery) return []
  if (delivery.options?.length) {
    return delivery.options.map((o) => ({ id: o.value, label: o.label }))
  }
  const items = delivery.items_enum ?? delivery.enum_items ?? []
  return items.map((id) => ({ id, label: id }))
}

export function normalizeAdminSections(
  sections: AdminSectionDef[] | undefined,
): AdminSectionDef[] {
  return (sections ?? []).map((s) => ({
    id: s.id,
    source: s.source,
    label_zh: s.label_zh || s.id,
  }))
}

/**
 * Normalize API payload into a UI-ready definition.
 * Throws on missing critical contract pieces — callers must surface the error (no fallback).
 */
export function normalizeWorkbenchDefinition(
  raw: WorkbenchFormApiResponse,
): WorkbenchDefinition {
  if (!raw?.project_settings?.fields || !raw?.project_settings?.groups) {
    throw new Error('工作台定义缺少 project_settings')
  }
  if (!Array.isArray(raw.stages) || raw.stages.length === 0) {
    throw new Error('工作台定义缺少 stages')
  }
  if (!raw.module_catalog) {
    throw new Error('工作台定义缺少 module_catalog')
  }

  const skills_bundle_version =
    raw.skills_bundle_version || raw.bundle_version || ''
  if (!skills_bundle_version) {
    throw new Error('工作台定义缺少 skills_bundle_version')
  }

  const fields: Record<string, SettingsFieldDef> = {}
  for (const [key, def] of Object.entries(raw.project_settings.fields)) {
    fields[key] = normalizeSettingsField(key, def)
  }

  const stages = normalizeStages(raw.stages)
  const modules = normalizeModules(raw.module_catalog)
  const groups = normalizeGroups(raw.project_settings.groups)
  const theme_matrix = buildThemeMatrixFromFields(fields, raw.theme_matrix ?? null)

  return {
    schema_version: raw.schema_version || 'workbench-form.v1',
    skills_bundle_version,
    groups,
    fields,
    stages,
    modules,
    module_panel: raw.module_panel,
    admin_sections: normalizeAdminSections(raw.admin_settings?.sections),
    theme_matrix,
    delivery_tab_items: deliveryTabsFromFields(fields),
  }
}

export function workbenchFormQueryKey(skillsBundleVersion?: string) {
  return skillsBundleVersion
    ? (['meta', 'workbench-form', skillsBundleVersion] as const)
    : (['meta', 'workbench-form'] as const)
}
