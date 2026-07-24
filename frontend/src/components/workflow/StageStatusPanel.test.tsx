import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import type { CommandRunSummary } from '@/types/v3/domain'
import { StageStatusPanel } from './StageStatusPanel'

function makeRun(overrides: Partial<CommandRunSummary> = {}): CommandRunSummary {
  return {
    id: 'run-1',
    command_type: 'generate_topic_brief',
    status: overrides.status ?? 'succeeded',
    project_id: 'p1',
    error_message: overrides.error_message ?? '',
    result_payload: {},
    created_at: '2026-07-24T00:00:00Z',
    updated_at: '2026-07-24T00:00:00Z',
  }
}

describe('StageStatusPanel', () => {
  it('shows generate succeeded hint and next-step link', () => {
    render(
      <MemoryRouter>
        <StageStatusPanel
          run={makeRun({ status: 'succeeded' })}
          generateSucceededHint="生成已完成，可预览候选并确认采用。"
          nextStep={{ to: '/projects/p1/blueprint', label: '去故事蓝图' }}
        />
      </MemoryRouter>,
    )

    expect(screen.getByText(/生成已完成/)).toBeInTheDocument()
    const next = screen.getByTestId('stage-next-step')
    expect(next).toHaveTextContent('去故事蓝图')
    expect(screen.getByRole('link', { name: '去故事蓝图' })).toHaveAttribute(
      'href',
      '/projects/p1/blueprint',
    )
  })

  it('shows prerequisite link when blocked', () => {
    render(
      <MemoryRouter>
        <StageStatusPanel
          prerequisite={{
            message: '请先确认选题简报。',
            to: '/projects/p1/topic',
            linkLabel: '去选题定调',
          }}
        />
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: '去选题定调' })).toHaveAttribute(
      'href',
      '/projects/p1/topic',
    )
  })
})
