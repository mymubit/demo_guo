import { evaluateCondition, settingsConditionContext } from '@/utils/conditions'
import type { ProjectSettings } from '@/types/domain'
import type { ModuleCatalogItem, StageDefinition, WorkbenchDefinition } from '@/types/workbench'

export function modulesForStage(
  modules: ModuleCatalogItem[],
  stage: StageDefinition | null | undefined,
  settings: ProjectSettings | null | undefined,
): ModuleCatalogItem[] {
  if (!stage || !settings) return []
  const ctx = settingsConditionContext({
    entry_type: settings.entry_type,
    enable_delivery: settings.creation_preferences.enable_delivery,
    creation_preferences: settings.creation_preferences,
    delivery_items: settings.creation_preferences.delivery_items,
    deliverables: settings.creation_preferences.delivery_items,
  })

  return modules.filter((m) => {
    if (m.lifecycle !== 'active' || !m.workbench_visible) return false
    if (!m.target_roles.includes(stage.role)) return false
    return evaluateCondition(m.enable_when, ctx)
  })
}

export function modulesForStageFromDefinition(
  definition: Pick<WorkbenchDefinition, 'modules'>,
  stage: StageDefinition | null | undefined,
  settings: ProjectSettings | null | undefined,
): ModuleCatalogItem[] {
  return modulesForStage(definition.modules, stage, settings)
}

export function groupModulesByDomain(modules: ModuleCatalogItem[]) {
  const map = new Map<string, ModuleCatalogItem[]>()
  for (const m of modules) {
    const list = map.get(m.domain) ?? []
    list.push(m)
    map.set(m.domain, list)
  }
  return Array.from(map.entries())
}
