import { getByPath, setByPath } from '@/utils/cn'
import { evaluateCondition, settingsConditionContext } from '@/utils/conditions'
import { SETTINGS_FIELDS, SETTINGS_GROUPS } from '@/config/workbench'
import type { ProjectSettings } from '@/types/domain'
import type { SettingsFieldDef } from '@/types/workbench'

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

export function visibleGroups(settings: ProjectSettings) {
  return SETTINGS_GROUPS.map((group) => ({
    ...group,
    fields: group.fields
      .map((key) => SETTINGS_FIELDS[key])
      .filter((f): f is SettingsFieldDef => Boolean(f) && isFieldVisible(f, settings)),
  })).filter((g) => g.fields.length > 0)
}

export function createDefaultSettings(partial?: Partial<ProjectSettings>): ProjectSettings {
  return {
    schema_version: 'project-settings.v1',
    entry_type: 'original_track',
    episode_count: 80,
    target_platform: 'generic',
    core_idea: '',
    production_context: {
      target_band: 'standard',
    },
    creation_preferences: {
      batch_episode_max: 5,
      outline_mode: 'full',
      scoring_preset: 'standard',
      compliance_check_mode: 'standard',
      enable_delivery: false,
      delivery_items: ['storyboard', 'visual', 'marketing', 'budget'],
    },
    flavor_tags: [],
    reference_dramas: [],
    audit: {
      revision: 1,
      updated_at: new Date().toISOString(),
      updated_by: 'user',
    },
    ...partial,
  }
}
