import type { ProjectStage } from '@/types/v3/domain'
import { STAGE_LABEL } from './projectLabels'

/** 创作主链阶段顺序（与看板一致） */
export const STAGE_PATH_ORDER: ProjectStage[] = [
  'topic',
  'blueprint',
  'episodes',
  'writing',
  'quality',
  'delivery',
]

/** URL 段 → stage；writing 使用 editor */
const SEGMENT_TO_STAGE: Record<string, ProjectStage> = {
  topic: 'topic',
  blueprint: 'blueprint',
  episodes: 'episodes',
  editor: 'writing',
  quality: 'quality',
  delivery: 'delivery',
}

const STAGE_TO_SEGMENT: Record<ProjectStage, string> = {
  topic: 'topic',
  blueprint: 'blueprint',
  episodes: 'episodes',
  writing: 'editor',
  quality: 'quality',
  delivery: 'delivery',
}

export function pathSegmentForStage(stage: ProjectStage): string {
  return STAGE_TO_SEGMENT[stage]
}

export function stageFromPathSegment(segment: string | undefined): ProjectStage | null {
  if (!segment) return null
  return SEGMENT_TO_STAGE[segment] ?? null
}

export function pathForStage(projectId: string, stage: ProjectStage): string {
  return `/projects/${projectId}/${pathSegmentForStage(stage)}`
}

export function settingsPath(projectId: string): string {
  return `/projects/${projectId}/settings`
}

export function adjacentStage(
  stage: ProjectStage,
  direction: -1 | 1,
): ProjectStage | null {
  const index = STAGE_PATH_ORDER.indexOf(stage)
  if (index < 0) return null
  const next = STAGE_PATH_ORDER[index + direction]
  return next ?? null
}

export function stageStepLabel(stage: ProjectStage): string {
  return STAGE_LABEL[stage]
}

export function stageIndex(stage: ProjectStage): number {
  return STAGE_PATH_ORDER.indexOf(stage)
}
