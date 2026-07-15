import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PipelineRail } from '@/components/workbench/PipelineRail'
import { WorkbenchDefinitionTestProvider } from '@/hooks/useWorkbenchDefinition'
import { testProjectSettings, testWorkbenchDefinition } from '@/test/workbenchFixtures'
import type { WorkflowState } from '@/types/domain'

const baseWorkflow: WorkflowState = {
  schema_version: 'workflow-state.v1',
  project_id: 'p1',
  version: 1,
  entry_type: 'original_track',
  status: 'waiting_quality',
  current_phase: 'quality',
  approvals: {},
  batch_cursor: 1,
  revision_round: 0,
  score_history: [],
  quality_results: {},
  artifacts: {},
  processed_commands: [],
}

const definition = testWorkbenchDefinition()

function renderRail(workflow: WorkflowState, activeStageId: string, settings = testProjectSettings()) {
  return render(
    <WorkbenchDefinitionTestProvider definition={definition}>
      <PipelineRail
        settings={settings}
        workflow={workflow}
        activeStageId={activeStageId}
        onSelect={() => undefined}
      />
    </WorkbenchDefinitionTestProvider>,
  )
}

describe('PipelineRail', () => {
  it('renders quality loop group labels from API definition and hides delivery when disabled', () => {
    renderRail(
      baseWorkflow,
      'quality_score',
      testProjectSettings({
        creation_preferences: {
          batch_episode_max: 5,
          outline_mode: 'full',
          scoring_preset: 'standard',
          compliance_check_mode: 'standard',
          enable_delivery: false,
        },
      }),
    )

    expect(screen.getByText('质检环')).toBeInTheDocument()
    expect(screen.getByText('质量评分报告')).toBeInTheDocument()
    expect(screen.getByText('合规审查报告')).toBeInTheDocument()
    expect(screen.getByText('修复稿')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /制作发行交付包/ })).toBeNull()
    expect(screen.getByRole('button', { name: /分集剧本/ })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: /立项简报/ })).not.toBeDisabled()
  })

  it('disables locked stages with aria-disabled', () => {
    renderRail(
      {
        ...baseWorkflow,
        status: 'active',
        current_phase: 'strategy',
      },
      'strategy',
    )

    const writing = screen.getByRole('button', { name: /分集剧本/ })
    expect(writing).toBeDisabled()
    expect(writing).toHaveAttribute('aria-disabled', 'true')
  })
})
