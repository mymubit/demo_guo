import { describe, expect, it } from 'vitest'
import { resolveUiWidget } from '@/config/workbench'
import {
  buildThemeMatrixFromFields,
  deliveryTabsFromFields,
  normalizeModules,
  normalizeSettingsField,
  normalizeStages,
  normalizeWorkbenchDefinition,
  workbenchFormQueryKey,
} from '@/utils/workbenchDefinition'
import { visibleGroups, isFieldVisible, isFieldRequired } from '@/utils/settingsForm'
import {
  mainPipelineStages,
  qualityLoopStages,
  visibleStages,
  workbenchStages,
  canExecuteStage,
  resolveStageStatus,
} from '@/utils/pipeline'
import { modulesForStageFromDefinition } from '@/utils/modules'
import {
  testProjectSettings,
  testWorkbenchDefinition,
  testWorkbenchFormApi,
} from '@/test/workbenchFixtures'
import type { ArtifactRecord, WorkflowState } from '@/types/domain'

function workflow(partial: Partial<WorkflowState>): WorkflowState {
  return {
    schema_version: 'workflow-state.v1',
    project_id: 'p1',
    version: 1,
    entry_type: 'original_track',
    status: 'active',
    current_phase: 'strategy',
    approvals: {},
    batch_cursor: 1,
    revision_round: 0,
    score_history: [],
    quality_results: {},
    artifacts: {},
    processed_commands: [],
    ...partial,
  }
}

describe('dynamic workbench-form contract', () => {
  it('1. requires skills_bundle_version and rejects missing payload', () => {
    expect(() =>
      normalizeWorkbenchDefinition({
        ...testWorkbenchFormApi(),
        skills_bundle_version: undefined,
        bundle_version: undefined,
      }),
    ).toThrow(/skills_bundle_version/)
    expect(() =>
      normalizeWorkbenchDefinition({
        schema_version: 'workbench-form.v1',
        skills_bundle_version: '1',
        project_settings: { groups: {}, fields: {} },
        stages: [],
        module_catalog: {},
      }),
    ).toThrow(/stages/)
  })

  it('2. partitions query cache key by skills bundle version', () => {
    expect(workbenchFormQueryKey()).toEqual(['meta', 'workbench-form'])
    expect(workbenchFormQueryKey('5.0.0')).toEqual(['meta', 'workbench-form', '5.0.0'])
    expect(workbenchFormQueryKey('5.1.0')).not.toEqual(workbenchFormQueryKey('5.0.0'))
  })

  it('3. merges backend stage artifact Chinese labels without frontend enum copy', () => {
    const stages = normalizeStages(testWorkbenchFormApi().stages)
    expect(stages.find((s) => s.id === 'blueprint')).toMatchObject({
      artifact: 'story_bible',
      label_zh: '故事蓝图',
    })
    expect(() =>
      normalizeStages([{ id: 'x', stage_kind: 'main', role: 'r', artifact: 'a' }]),
    ).toThrow(/label_zh/)
    expect(() =>
      normalizeStages([{ id: 'x', stage_kind: 'main', role: 'r', label_zh: '标签' }]),
    ).toThrow(/artifact/)
  })

  it('4. normalizes module_catalog object map into list', () => {
    const modules = normalizeModules(testWorkbenchFormApi().module_catalog)
    expect(modules.some((m) => m.id === 'concept-development')).toBe(true)
    expect(modules.find((m) => m.id === 'adaptation-originality')?.enable_when).toContain(
      'story_adapt',
    )
  })

  it('5. drives settings fields from parameter contract parse result', () => {
    const field = normalizeSettingsField('entry_type', testWorkbenchFormApi().project_settings.fields.entry_type)
    expect(field.ui_widget).toBe('select')
    expect(field.options?.map((o) => o.value)).toEqual(['original_track', 'story_adapt'])
    expect(field.default).toBe('original_track')

    const delivery = normalizeSettingsField(
      'delivery_items',
      testWorkbenchFormApi().project_settings.fields.delivery_items,
    )
    expect(delivery.ui_widget).toBe('checklist')
    expect(delivery.options?.map((o) => o.value)).toContain('storyboard')
  })

  it('6. resolves UI widgets without hardcoding business enums', () => {
    expect(resolveUiWidget({ type: 'boolean' })).toBe('switch')
    expect(resolveUiWidget({ type: 'integer' })).toBe('number')
    expect(resolveUiWidget({ type: 'array', items_enum: ['a'] })).toBe('checklist')
    expect(resolveUiWidget({ type: 'object', fields: { a: {} } })).toBe('matrix')
    expect(resolveUiWidget({ type: 'string', enum: ['a'] })).toBe('select')
    expect(resolveUiWidget({ type: 'string', ui_widget: 'textarea' })).toBe('textarea')
  })

  it('7. builds theme matrix from genre_matrix / flavor_tags field contracts', () => {
    const def = testWorkbenchDefinition()
    expect(def.theme_matrix).not.toBeNull()
    expect(def.theme_matrix?.dim_order).toEqual(['emotion', 'identity', 'conflict', 'world'])
    expect(def.theme_matrix?.axes.emotion.options[0].label_zh).toBe('复仇爽感')
    expect(def.theme_matrix?.flavor_tags.max_select).toBe(5)
    expect(def.theme_matrix?.preset_templates?.[0].code).toBe('family-revenge')

    const rebuilt = buildThemeMatrixFromFields(def.fields, null)
    expect(rebuilt?.axes.world.options.map((o) => o.value)).toContain('urban')
  })

  it('8. derives delivery tabs from delivery_items contract', () => {
    const def = testWorkbenchDefinition()
    const tabs = deliveryTabsFromFields(def.fields)
    expect(tabs.map((t) => t.id)).toEqual([
      'storyboard',
      'visual',
      'marketing',
      'interactive',
      'budget',
      'release',
    ])
  })

  it('9. filters settings groups/fields by visible_when from API definition', () => {
    const def = testWorkbenchDefinition()
    const original = testProjectSettings({ entry_type: 'original_track' })
    const adapt = testProjectSettings({ entry_type: 'story_adapt', external_story: 'x' })

    expect(isFieldVisible(def.fields.core_idea, original)).toBe(true)
    expect(isFieldVisible(def.fields.external_story, original)).toBe(false)
    expect(isFieldVisible(def.fields.core_idea, adapt)).toBe(false)
    expect(isFieldRequired(def.fields.external_story, adapt)).toBe(true)

    const groups = visibleGroups(def, original)
    expect(groups.find((g) => g.id === 'entry')?.fields.map((f) => f.key)).toContain('core_idea')
    expect(groups.find((g) => g.id === 'entry')?.fields.map((f) => f.key)).not.toContain(
      'external_story',
    )

    const off = testProjectSettings({
      creation_preferences: {
        ...original.creation_preferences,
        enable_delivery: false,
      },
    })
    const on = testProjectSettings({
      creation_preferences: {
        ...original.creation_preferences,
        enable_delivery: true,
      },
    })
    expect(isFieldVisible(def.fields.delivery_items, off)).toBe(false)
    expect(isFieldVisible(def.fields.delivery_items, on)).toBe(true)
  })

  it('10. drives pipeline stages from API definition (no static STAGES)', () => {
    const def = testWorkbenchDefinition()
    const adapt = visibleStages(def.stages, { entry_type: 'story_adapt', enable_delivery: false })
    expect(adapt.some((s) => s.id === 'strategy')).toBe(false)
    expect(adapt.some((s) => s.id === 'delivery')).toBe(false)

    const withDelivery = mainPipelineStages(def.stages, {
      entry_type: 'original_track',
      enable_delivery: true,
      creation_preferences: { enable_delivery: true, delivery_items: ['budget'] },
    })
    expect(withDelivery.some((s) => s.id === 'delivery')).toBe(true)
    expect(withDelivery.find((s) => s.id === 'delivery')?.label_zh).toBe('制作发行交付包')

    const loop = qualityLoopStages(def.stages, { entry_type: 'original_track' })
    expect(loop.map((s) => s.id)).toEqual(['quality_score', 'compliance', 'revision'])
    expect(workbenchStages(def, { entry_type: 'original_track' }).length).toBeGreaterThan(3)
  })

  it('11. resolves stage status / execute gate using definition stages', () => {
    const def = testWorkbenchDefinition()
    const stages = visibleStages(def.stages, { entry_type: 'original_track' })
    const blueprint = stages.find((s) => s.id === 'blueprint')!
    const strategy = stages.find((s) => s.id === 'strategy')!
    const quality = stages.find((s) => s.id === 'quality_score')!

    expect(resolveStageStatus(strategy, workflow({ current_phase: 'blueprint' }))).toBe('done')
    expect(
      resolveStageStatus(
        blueprint,
        workflow({ current_phase: 'blueprint_approval', status: 'waiting_approval' }),
      ),
    ).toBe('waiting')
    expect(
      canExecuteStage(strategy, workflow({ current_phase: 'strategy', status: 'active' })),
    ).toBe(true)
    expect(
      canExecuteStage(
        quality,
        workflow({ current_phase: 'quality', status: 'waiting_user' }),
      ),
    ).toBe(false)
  })

  it('12. filters modules from API catalog by role and enable_when', () => {
    const def = testWorkbenchDefinition()
    const strategy = def.stages.find((s) => s.id === 'strategy')!
    const blueprint = def.stages.find((s) => s.id === 'blueprint')!
    const delivery = def.stages.find((s) => s.id === 'delivery')!

    const original = testProjectSettings({ entry_type: 'original_track' })
    const adapt = testProjectSettings({ entry_type: 'story_adapt' })
    const withDelivery = testProjectSettings({
      creation_preferences: {
        batch_episode_max: 5,
        outline_mode: 'full',
        scoring_preset: 'standard',
        compliance_check_mode: 'standard',
        enable_delivery: true,
        delivery_items: ['storyboard'],
      },
    })

    expect(modulesForStageFromDefinition(def, strategy, original).map((m) => m.id)).toContain(
      'concept-development',
    )
    expect(modulesForStageFromDefinition(def, blueprint, original).map((m) => m.id)).not.toContain(
      'adaptation-originality',
    )
    expect(modulesForStageFromDefinition(def, blueprint, adapt).map((m) => m.id)).toContain(
      'adaptation-originality',
    )
    expect(modulesForStageFromDefinition(def, delivery, withDelivery).map((m) => m.id)).toContain(
      'storyboard-9col',
    )
  })

  it('13. ArtifactRecord.schema_version is numeric (not story-bible.v1 string)', () => {
    const record: ArtifactRecord<{ title: string }> = {
      artifact_key: 'story_bible',
      version: 1,
      schema_version: 1,
      payload: { title: 'demo' },
    }
    expect(typeof record.schema_version).toBe('number')
    expect(record.schema_version).toBe(1)
    // Ensure we do not type/parse legacy story-bible.v1 string identifiers
    const _assertNumber: number | undefined = record.schema_version
    expect(_assertNumber).toBe(1)
  })

  it('14. admin sections and normalize end-to-end preserve bundle version', () => {
    const def = normalizeWorkbenchDefinition(testWorkbenchFormApi({ skills_bundle_version: '5.2.1' }))
    expect(def.skills_bundle_version).toBe('5.2.1')
    expect(def.admin_sections.map((s) => s.id)).toEqual(['model_routing', 'script_format'])
    expect(def.schema_version).toBe('workbench-form.v1')
  })
})
