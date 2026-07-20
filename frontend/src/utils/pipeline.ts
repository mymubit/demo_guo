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
  creation_preferences?: { enable_delivery?: boolean; deliverables?: string[] }
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

  // 误入待审批但无蓝图：按入口阶段展示，避免整条流水线假锁死
  let current = workflow.current_phase
  if (
    workflow.status === 'waiting_approval' &&
    !workflow.artifacts?.story_bible &&
    current === 'blueprint_approval'
  ) {
    current = workflow.entry_type === 'story_adapt' ? 'blueprint' : 'strategy'
  }

  if (target === 'blueprint' && (current === 'blueprint' || current === 'blueprint_approval')) {
    if (workflow.status === 'waiting_approval' && workflow.artifacts?.story_bible) {
      return 'waiting'
    }
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
  return explainExecuteGate(stage, workflow) === null
}

/** 返回不可执行的中文原因；可执行时返回 null */
export function explainExecuteGate(
  stage: StageDefinition,
  workflow: WorkflowState | null | undefined,
): string | null {
  if (!workflow) return '工作流尚未加载，请稍后重试。'
  if (workflow.status === 'blocked') {
    return workflow.blocked_reason
      ? `流程已阻塞：${workflow.blocked_reason}`
      : '流程已阻塞，请检查创作设定或上一步产物。'
  }
  if (workflow.status === 'completed') return '项目已完成，无需再执行本阶段。'
  if (workflow.status === 'waiting_approval') {
    const hasBible = Boolean(workflow.artifacts?.story_bible)
    if (hasBible) {
      return '故事蓝图待审批：请先在蓝图阶段通过或驳回后再继续。'
    }
    // 异常卡住：待审批但无蓝图产物 —— 不拦截执行，落到下方阶段状态判断
  }
  if (workflow.status === 'waiting_user') {
    return '质检环等待你的决策：请先在质量面板选择修订或放行。'
  }
  const status = resolveStageStatus(stage, workflow)
  if (status === 'active') return null
  if (status === 'locked') {
    return `「${stage.label_zh}」尚未解锁。请先完成流水线中更靠前的阶段。`
  }
  if (status === 'done') return `「${stage.label_zh}」已完成。如需重跑，请从对应阶段重新发起。`
  if (status === 'waiting') return `「${stage.label_zh}」正在等待外部操作（审批或决策）。`
  if (status === 'blocked') return `「${stage.label_zh}」当前不可用。`
  return `「${stage.label_zh}」暂不可执行。`
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
