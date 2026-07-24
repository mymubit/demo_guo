import type { ProjectEntryType, ProjectStage } from '@/types/v3/domain'
import { adjacentStage, pathForStage } from './projectStagePaths'

export const STAGE_LABEL: Record<ProjectStage, string> = {
  topic: '选题定调',
  blueprint: '故事蓝图',
  episodes: '分集规划',
  writing: '剧本正文',
  quality: '质检修订',
  delivery: '制作交付',
}

export const ENTRY_LABEL: Record<ProjectEntryType, string> = {
  original: '原创',
  adapt: '改编',
}

/** 概览页阶段主 CTA：可导航链接，或后续阶段占位。 */
export type OverviewStageCta =
  | { kind: 'link'; to: string; label: string }
  | { kind: 'placeholder'; label: '后续开放' }

export function resolveOverviewStageCta(
  projectId: string,
  stage: ProjectStage,
): OverviewStageCta {
  switch (stage) {
    case 'topic':
      return { kind: 'link', to: pathForStage(projectId, 'topic'), label: '去选题定调' }
    case 'blueprint':
      return { kind: 'link', to: pathForStage(projectId, 'blueprint'), label: '去故事蓝图' }
    case 'episodes':
      return { kind: 'link', to: pathForStage(projectId, 'episodes'), label: '去分集规划' }
    case 'writing':
      return { kind: 'link', to: pathForStage(projectId, 'writing'), label: '去正文编辑' }
    case 'quality':
      return { kind: 'link', to: pathForStage(projectId, 'quality'), label: '去质检中心' }
    case 'delivery':
      return { kind: 'link', to: pathForStage(projectId, 'delivery'), label: '去交付中心' }
  }
}

/** 当前阶段完成后，引导进入的下一阶段 CTA；已是最后一阶段则 null。 */
export function resolveNextStageCta(
  projectId: string,
  currentStage: ProjectStage,
): Extract<OverviewStageCta, { kind: 'link' }> | null {
  const next = adjacentStage(currentStage, 1)
  if (!next) return null
  const cta = resolveOverviewStageCta(projectId, next)
  return cta.kind === 'link' ? cta : null
}
