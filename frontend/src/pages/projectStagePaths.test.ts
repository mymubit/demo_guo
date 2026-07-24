import { describe, expect, it } from 'vitest'
import {
  adjacentStage,
  pathForStage,
  pathSegmentForStage,
  settingsPath,
  stageFromPathSegment,
  STAGE_PATH_ORDER,
} from './projectStagePaths'

describe('projectStagePaths', () => {
  it('maps writing stage to editor segment', () => {
    expect(pathSegmentForStage('writing')).toBe('editor')
    expect(stageFromPathSegment('editor')).toBe('writing')
    expect(pathForStage('p1', 'writing')).toBe('/projects/p1/editor')
  })

  it('walks adjacent stages in order', () => {
    expect(adjacentStage('topic', 1)).toBe('blueprint')
    expect(adjacentStage('topic', -1)).toBeNull()
    expect(adjacentStage('delivery', 1)).toBeNull()
    expect(adjacentStage('quality', -1)).toBe('writing')
  })

  it('exposes six-step order and settings path', () => {
    expect(STAGE_PATH_ORDER).toHaveLength(6)
    expect(settingsPath('abc')).toBe('/projects/abc/settings')
  })
})
