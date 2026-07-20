import { describe, expect, it } from 'vitest'
import {
  canExecuteStage,
  explainExecuteGate,
  isQualityPhaseHighlight,
  mainPipelineStages,
  qualityLoopStages,
  resolveStageStatus,
  visibleStages,
  workbenchStages,
} from '@/utils/pipeline'
import { testWorkbenchDefinition } from '@/test/workbenchFixtures'
import type { WorkflowState } from '@/types/domain'

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

describe('pipeline status (definition-driven)', () => {
  const definition = testWorkbenchDefinition()

  it('hides strategy for story_adapt and delivery when disabled', () => {
    const adaptStages = visibleStages(definition.stages, {
      entry_type: 'story_adapt',
      enable_delivery: false,
    })
    expect(adaptStages.some((s) => s.id === 'strategy')).toBe(false)
    expect(adaptStages.some((s) => s.id === 'delivery')).toBe(false)

    const withDelivery = mainPipelineStages(definition.stages, {
      entry_type: 'original_track',
      enable_delivery: true,
      creation_preferences: { enable_delivery: true, delivery_items: ['budget'] },
    })
    expect(withDelivery.some((s) => s.id === 'delivery')).toBe(true)
  })

  it('marks past phases done and current active/waiting', () => {
    const stages = visibleStages(definition.stages, {
      entry_type: 'original_track',
      enable_delivery: false,
    })
    const blueprint = stages.find((s) => s.id === 'blueprint')!
    const strategy = stages.find((s) => s.id === 'strategy')!

    expect(resolveStageStatus(strategy, workflow({ current_phase: 'blueprint' }))).toBe('done')
    expect(resolveStageStatus(blueprint, workflow({ current_phase: 'blueprint' }))).toBe('active')
    expect(
      resolveStageStatus(
        blueprint,
        workflow({
          current_phase: 'blueprint_approval',
          status: 'waiting_approval',
          artifacts: { story_bible: { version: 1 } },
        }),
      ),
    ).toBe('waiting')
    expect(
      resolveStageStatus(
        strategy,
        workflow({ current_phase: 'blueprint_approval', status: 'waiting_approval', artifacts: {} }),
      ),
    ).toBe('active')
  })

  it('marks quality waiting_user as waiting', () => {
    const stages = visibleStages(definition.stages, { entry_type: 'original_track' })
    const quality = stages.find((s) => s.id === 'quality_score')!
    expect(
      resolveStageStatus(
        quality,
        workflow({ current_phase: 'quality', status: 'waiting_user' }),
      ),
    ).toBe('waiting')
  })

  it('exposes quality_score / compliance / revision as quality loop group', () => {
    const loop = qualityLoopStages(definition.stages, { entry_type: 'original_track' })
    expect(loop.map((s) => s.id)).toEqual(['quality_score', 'compliance', 'revision'])
    const all = workbenchStages(definition, { entry_type: 'original_track', enable_delivery: false })
    expect(all.some((s) => s.id === 'quality_score')).toBe(true)
  })

  it('highlights quality/revision phases', () => {
    expect(isQualityPhaseHighlight(workflow({ current_phase: 'quality' }))).toBe(true)
    expect(isQualityPhaseHighlight(workflow({ current_phase: 'revision' }))).toBe(true)
    expect(isQualityPhaseHighlight(workflow({ current_phase: 'writing' }))).toBe(false)
    expect(
      isQualityPhaseHighlight(workflow({ current_phase: 'writing', status: 'waiting_user' })),
    ).toBe(true)
  })

  it('gates execute strictly by phase/status/stage', () => {
    const stages = visibleStages(definition.stages, { entry_type: 'original_track' })
    const strategy = stages.find((s) => s.id === 'strategy')!
    const writing = stages.find((s) => s.id === 'writing')!
    const quality = stages.find((s) => s.id === 'quality_score')!

    expect(canExecuteStage(strategy, workflow({ current_phase: 'strategy', status: 'active' }))).toBe(
      true,
    )
    expect(canExecuteStage(writing, workflow({ current_phase: 'strategy', status: 'active' }))).toBe(
      false,
    )
    expect(
      canExecuteStage(strategy, workflow({ current_phase: 'strategy', status: 'waiting_approval' })),
    ).toBe(true)
    expect(
      canExecuteStage(
        strategy,
        workflow({
          current_phase: 'strategy',
          status: 'waiting_approval',
          artifacts: { story_bible: { version: 1 } },
        }),
      ),
    ).toBe(false)
    expect(
      canExecuteStage(
        quality,
        workflow({ current_phase: 'quality', status: 'waiting_user' }),
      ),
    ).toBe(false)
    expect(
      canExecuteStage(quality, workflow({ current_phase: 'quality', status: 'waiting_quality' })),
    ).toBe(true)
  })

  it('explains execute gate in Chinese', () => {
    const stages = visibleStages(definition.stages, { entry_type: 'original_track' })
    const strategy = stages.find((s) => s.id === 'strategy')!
    const writing = stages.find((s) => s.id === 'writing')!

    expect(explainExecuteGate(strategy, workflow({ current_phase: 'strategy', status: 'active' }))).toBe(
      null,
    )
    expect(
      explainExecuteGate(writing, workflow({ current_phase: 'strategy', status: 'active' })),
    ).toMatch(/尚未解锁/)
    expect(
      explainExecuteGate(
        strategy,
        workflow({
          current_phase: 'strategy',
          status: 'waiting_approval',
          artifacts: { story_bible: { version: 1 } },
        }),
      ),
    ).toMatch(/待审批/)
    expect(
      explainExecuteGate(
        strategy,
        workflow({ current_phase: 'blueprint_approval', status: 'waiting_approval', artifacts: {} }),
      ),
    ).toBe(null)
  })
})
