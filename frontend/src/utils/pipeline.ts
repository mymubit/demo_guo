import { evaluateCondition, settingsConditionContext } from '@/utils/conditions'
import type { StageDefinition, WorkbenchDefinition } from '@/types/workbench'
import type { WorkflowPhase, WorkflowState } from '@/types/domain'

export type StageRailStatus = 'locked' | 'pending' | 'active' | 'waiting' | 'done' | 'blocked'

const PHASE_ORDER: WorkflowPhase[] = [
  'strategy',
  'blueprint',
  'blueprint_approval',
  'episode_design',
  'writing',
  'quality',
  'revision',
  'delivery',
  'completed',
]

function phaseIndex(phase: WorkflowPhase): number {
  return PHASE_ORDER.indexOf(phase)
}

function stagePhase(stage: StageDefinition): WorkflowPhase | null {
  if (stage.orchestration_phase) {
    const phase = stage.orchestration_phase as WorkflowPhase
    if (PHASE_ORDER.includes(phase)) return phase
  }
  if (stage.id === 'strategy') return 'strategy'
  if (stage.id === 'blueprint') return 'blueprint'
  if (stage.id === 'episode_design') return 'episode_design'
  if (stage.id === 'writing') return 'writing'
  if (stage.stage_kind === 'quality_loop') {
    if (stage.id === 'revision') return 'revision'
    return 'quality'
  }
  if (stage.id === 'delivery') return 'delivery'
  return null
}

type StageFilterCtx = {
  entry_type?: string
  enable_delivery?: boolean
  creation_preferences?: { enable_delivery?: boolean; delivery_items?: string[] }
}

export function visibleStages(
  stages: StageDefinition[],
  ctx: StageFilterCtx,
): StageDefinition[] {
  const conditionCtx = settingsConditionContext(ctx)
  return stages.filter((s) => evaluateCondition(s.visible_when, conditionCtx))
}

export function resolveStageStatus(
  stage: StageDefinition,
  workflow: WorkflowState | null | undefined,
): StageRailStatus {
  if (!workflow) return 'pending'
  if (workflow.status === 'blocked') return 'blocked'

  const target = stagePhase(stage)
  if (!target) return 'pending'

  const current = workflow.current_phase

  if (target === 'blueprint' && (current === 'blueprint' || current === 'blueprint_approval')) {
    if (workflow.status === 'waiting_approval') return 'waiting'
    return 'active'
  }

  if (
    target === 'quality' &&
    (current === 'quality' ||
      workflow.status === 'waiting_quality' ||
      workflow.status === 'waiting_user')
  ) {
    if (workflow.status === 'waiting_user') return 'waiting'
    return 'active'
  }

  if (target === 'revision' && current === 'revision') {
    return 'active'
  }

  if (current === 'completed') return 'done'

  const curIdx = phaseIndex(current)
  const tgtIdx = phaseIndex(target)

  if (tgtIdx === curIdx) return 'active'
  if (curIdx > tgtIdx) return 'done'
  return 'locked'
}

/**
 * Execute gate: only the current active stage under an executable workflow status
 * may start generation. Locked / waiting / done / blocked stages are disabled.
 */
export function canExecuteStage(
  stage: StageDefinition,
  workflow: WorkflowState | null | undefined,
): boolean {
  if (!workflow) return false
  if (
    workflow.status === 'blocked' ||
    workflow.status === 'completed' ||
    workflow.status === 'waiting_approval' ||
    workflow.status === 'waiting_user'
  ) {
    return false
  }
  return resolveStageStatus(stage, workflow) === 'active'
}

export function isQualityPhaseHighlight(workflow: WorkflowState | null | undefined): boolean {
  if (!workflow) return false
  return (
    workflow.current_phase === 'quality' ||
    workflow.current_phase === 'revision' ||
    workflow.status === 'waiting_quality' ||
    workflow.status === 'waiting_user'
  )
}

export function mainPipelineStages(
  stages: StageDefinition[],
  ctx: StageFilterCtx,
): StageDefinition[] {
  return visibleStages(stages, ctx).filter(
    (s) => s.stage_kind === 'main' || s.stage_kind === 'optional',
  )
}

export function qualityLoopStages(
  stages: StageDefinition[],
  ctx: StageFilterCtx,
): StageDefinition[] {
  return visibleStages(stages, ctx).filter((s) => s.stage_kind === 'quality_loop')
}

/** All selectable stages for workbench canvas (main + quality loop + optional). */
export function workbenchStages(
  definition: Pick<WorkbenchDefinition, 'stages'>,
  ctx: StageFilterCtx,
): StageDefinition[] {
  return visibleStages(definition.stages, ctx)
}
