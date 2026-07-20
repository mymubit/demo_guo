import { describe, expect, it } from 'vitest'
import {
  isGenreMatrixComplete,
  isWorkflowFirstRun,
  resolveFirstRunStageId,
  shouldShowFirstRunExecuteGuide,
} from '@/utils/firstRunGuide'
import { testProjectSettings, testWorkbenchDefinition } from '@/test/workbenchFixtures'
import { workbenchStages } from '@/utils/pipeline'
import type { WorkflowState } from '@/types/domain'

function workflow(partial: Partial<WorkflowState> = {}): WorkflowState {
  return {
    schema_version: 'workflow-state.v1',
    project_id: 'p1',
    version: 0,
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

describe('firstRunGuide', () => {
  const definition = testWorkbenchDefinition()
  const stages = workbenchStages(definition, { entry_type: 'original_track' })

  it('detects complete genre matrix', () => {
    expect(isGenreMatrixComplete(undefined)).toBe(false)
    expect(
      isGenreMatrixComplete({ emotion: 'a', identity: 'b', conflict: 'c', world: 'd' }),
    ).toBe(true)
    expect(
      isGenreMatrixComplete({ emotion: 'a', identity: '', conflict: 'c', world: 'd' }),
    ).toBe(false)
  })

  it('detects empty workflow as first run', () => {
    expect(isWorkflowFirstRun(workflow())).toBe(true)
    expect(isWorkflowFirstRun(workflow({ version: 1, artifacts: { project_brief: {} } }))).toBe(
      false,
    )
  })

  it('resolves strategy as first-run stage for original track', () => {
    expect(resolveFirstRunStageId(stages, workflow())).toBe('strategy')
  })

  it('shows execute guide when core_idea or theme ready and stage executable', () => {
    const strategy = stages.find((s) => s.id === 'strategy')!
    const withTheme = testProjectSettings({
      core_idea: '',
      genre_matrix: { emotion: 'e', identity: 'i', conflict: 'c', world: 'w' },
    })
    const withIdeaOnly = testProjectSettings({
      core_idea: '一个逆袭故事',
      genre_matrix: undefined,
    })
    expect(
      shouldShowFirstRunExecuteGuide({
        settings: withTheme,
        workflow: workflow(),
        stage: strategy,
        hasPayload: false,
        executable: true,
      }),
    ).toBe(true)
    expect(
      shouldShowFirstRunExecuteGuide({
        settings: withIdeaOnly,
        workflow: workflow(),
        stage: strategy,
        hasPayload: false,
        executable: true,
      }),
    ).toBe(true)
    expect(
      shouldShowFirstRunExecuteGuide({
        settings: withTheme,
        workflow: workflow(),
        stage: strategy,
        hasPayload: true,
        executable: true,
      }),
    ).toBe(false)
  })
})
