import { getByPath, setByPath } from '@/utils/cn'
import { evaluateCondition, settingsConditionContext } from '@/utils/conditions'
import type { ProjectSettings } from '@/types/domain'
import type { SettingsFieldDef, WorkbenchDefinition } from '@/types/workbench'

export function isFieldVisible(field: SettingsFieldDef, settings: ProjectSettings): boolean {
  const ctx = settingsConditionContext({
    entry_type: settings.entry_type,
    enable_delivery: settings.creation_preferences?.enable_delivery,
    creation_preferences: settings.creation_preferences,
    delivery_items: settings.creation_preferences?.delivery_items,
  })
  return evaluateCondition(field.visible_when, ctx)
}

export function isFieldRequired(field: SettingsFieldDef, settings: ProjectSettings): boolean {
  if (field.required) return true
  const ctx = settingsConditionContext({
    entry_type: settings.entry_type,
    enable_delivery: settings.creation_preferences?.enable_delivery,
    creation_preferences: settings.creation_preferences,
  })
  return evaluateCondition(field.required_when, ctx)
}

export function readSettingValue(settings: ProjectSettings, field: SettingsFieldDef): unknown {
  return getByPath(settings, field.persist_path)
}

export function writeSettingValue(
  settings: ProjectSettings,
  field: SettingsFieldDef,
  value: unknown,
): ProjectSettings {
  const clone = structuredClone(settings) as ProjectSettings
  setByPath(clone as unknown as Record<string, unknown>, field.persist_path, value)
  return clone
}

export function visibleGroups(
  definition: Pick<WorkbenchDefinition, 'groups' | 'fields'>,
  settings: ProjectSettings,
) {
  return definition.groups
    .map((group) => ({
      ...group,
      fields: group.fields
        .map((key) => definition.fields[key])
        .filter((f): f is SettingsFieldDef => Boolean(f) && isFieldVisible(f, settings)),
    }))
    .filter((g) => g.fields.length > 0)
}

/**
 * Apply parameter-contract defaults from a loaded definition onto an existing settings object.
 * Does not invent business defaults — only copies `field.default` when present on the contract.
 */
export function applyFieldDefaults(
  definition: Pick<WorkbenchDefinition, 'fields'>,
  base: ProjectSettings,
): ProjectSettings {
  let next = base
  for (const field of Object.values(definition.fields)) {
    if (field.default === undefined) continue
    const current = readSettingValue(next, field)
    if (current === undefined || current === null) {
      next = writeSettingValue(next, field, field.default)
    }
  }
  return next
}
