import type { GenreMatrix, ProjectSettings, WorkflowState } from '@/types/domain'
import type { StageDefinition } from '@/types/workbench'
import { canExecuteStage, resolveStageStatus } from '@/utils/pipeline'

export function isGenreMatrixComplete(
  matrix: GenreMatrix | null | undefined,
): boolean {
  if (!matrix) return false
  return Boolean(matrix.emotion && matrix.identity && matrix.conflict && matrix.world)
}

/**
 * 选题定调官 required_params_any_of：core_idea | synopsis | genre_matrix
 * 改编通道编排要求：external_story
 */
export function hasTopicDirectorInput(
  settings: Pick<
    ProjectSettings,
    'entry_type' | 'core_idea' | 'synopsis' | 'external_story' | 'genre_matrix'
  >,
): boolean {
  if (settings.entry_type === 'story_adapt') {
    return Boolean(settings.external_story?.trim())
  }
  return Boolean(
    settings.core_idea?.trim() ||
      settings.synopsis?.trim() ||
      isGenreMatrixComplete(settings.genre_matrix),
  )
}

/** 主链尚未产生任何产物，视为首跑空台 */
export function isWorkflowFirstRun(workflow: WorkflowState | null | undefined): boolean {
  if (!workflow) return true
  const artifacts = workflow.artifacts ?? {}
  return Object.keys(artifacts).length === 0 && workflow.version === 0
}

/**
 * 首跑默认落点：优先可执行的当前阶段；否则取主链第一个未锁定阶段。
 * 原创通道通常是「立项简报 / strategy」。
 */
export function resolveFirstRunStageId(
  stages: StageDefinition[],
  workflow: WorkflowState | null | undefined,
): string | null {
  if (stages.length === 0) return null

  const executable = stages.find((s) => canExecuteStage(s, workflow))
  if (executable) return executable.id

  const unlocked = stages.find((s) => {
    const status = resolveStageStatus(s, workflow)
    return status !== 'locked' && status !== 'blocked'
  })
  return unlocked?.id ?? stages[0]?.id ?? null
}

export function shouldShowFirstRunExecuteGuide(input: {
  settings: ProjectSettings
  workflow: WorkflowState
  stage: StageDefinition
  hasPayload: boolean
  executable: boolean
  forceGuide?: boolean
}): boolean {
  const { settings, workflow, stage, hasPayload, executable, forceGuide } = input
  if (hasPayload || !executable) return false
  if (!hasTopicDirectorInput(settings)) return false
  if (forceGuide) return true
  if (!isWorkflowFirstRun(workflow)) return false
  return resolveStageStatus(stage, workflow) === 'active'
}
