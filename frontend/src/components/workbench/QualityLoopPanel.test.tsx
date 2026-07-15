import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { QualityLoopPanel } from '@/components/workbench/QualityLoopPanel'
import type { WorkflowState } from '@/types/domain'

vi.mock('@/services/drama', () => ({
  dramaApi: {
    postWorkflowCommand: vi.fn().mockResolvedValue({
      schema_version: 'workflow-state.v1',
      project_id: 'p1',
      version: 4,
      entry_type: 'original_track',
      status: 'active',
      current_phase: 'writing',
      approvals: {},
      batch_cursor: 2,
      revision_round: 0,
      score_history: [],
      quality_results: {},
      artifacts: {},
      processed_commands: [],
    }),
  },
}))

const baseWorkflow: WorkflowState = {
  schema_version: 'workflow-state.v1',
  project_id: 'p1',
  version: 3,
  entry_type: 'original_track',
  status: 'waiting_user',
  current_phase: 'quality',
  approvals: {},
  batch_cursor: 1,
  revision_round: 2,
  score_history: [70, 72],
  quality_results: {},
  artifacts: {},
  processed_commands: [],
  pending_user_options: ['accept_current', 'manual_revision', 'abandon_batch'],
}

describe('QualityLoopPanel waiting_user decisions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders three decision actions when waiting_user', async () => {
    const user = userEvent.setup()
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    })

    render(
      <QueryClientProvider client={client}>
        <QualityLoopPanel
          projectId="p1"
          workflow={baseWorkflow}
          qualityReport={{ overall_score: 72, grade: 'C', verdict: '需要修改' }}
          complianceReport={{ overall_result: '风险', blocking_issues: [], risk_items: [] }}
        />
      </QueryClientProvider>,
    )

    expect(screen.getByText('等待用户决策')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '接受当前批次' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '手动修复' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '放弃本批' })).toBeInTheDocument()
    expect(screen.getByText(/修复轮次/)).toHaveTextContent('2')

    await user.click(screen.getByRole('button', { name: '接受当前批次' }))
    const { dramaApi } = await import('@/services/drama')
    expect(dramaApi.postWorkflowCommand).toHaveBeenCalled()
  })
})
