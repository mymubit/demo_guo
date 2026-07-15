import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PipelineRail } from '@/components/workbench/PipelineRail'
import { createDefaultSettings } from '@/utils/settingsForm'
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

describe('PipelineRail', () => {
  it('renders quality_score / compliance / revision group and locks future stages', () => {
    const settings = createDefaultSettings({
      creation_preferences: {
        batch_episode_max: 5,
        outline_mode: 'full',
        scoring_preset: 'standard',
        compliance_check_mode: 'standard',
        enable_delivery: false,
      },
    })

    render(
      <PipelineRail
        settings={settings}
        workflow={baseWorkflow}
        activeStageId="quality_score"
        onSelect={() => undefined}
      />,
    )

    expect(screen.getByText('质检环')).toBeInTheDocument()
    expect(screen.getByText('评分')).toBeInTheDocument()
    expect(screen.getByText('合规')).toBeInTheDocument()
    expect(screen.getByText('修复')).toBeInTheDocument()

    const deliveryLocked = screen.queryByRole('button', { name: /宣发交付/ })
    // delivery hidden when enable_delivery false
    expect(deliveryLocked).toBeNull()

    const writingBtn = screen.getByRole('button', { name: /正文创作/ })
    // writing is past quality? writing is before quality so should be done, clickable
    expect(writingBtn).not.toBeDisabled()

    // strategy done
    expect(screen.getByRole('button', { name: /选题定调/ })).not.toBeDisabled()
  })

  it('disables locked stages with aria-disabled', () => {
    const settings = createDefaultSettings()
    const early: WorkflowState = {
      ...baseWorkflow,
      status: 'active',
      current_phase: 'strategy',
    }

    render(
      <PipelineRail
        settings={settings}
        workflow={early}
        activeStageId="strategy"
        onSelect={() => undefined}
      />,
    )

    const writing = screen.getByRole('button', { name: /正文创作/ })
    expect(writing).toBeDisabled()
    expect(writing).toHaveAttribute('aria-disabled', 'true')
  })
})
