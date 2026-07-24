import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ProjectSummary, SystemConfigState, UsageSummary } from '@/types/v3/domain'
import { getShanghaiDateString } from '@/utils/dailyCostAlert'
import { UsagePage } from './UsagePage'

const getUsageSummary = vi.fn()
const listProjects = vi.fn()
const getSystemConfig = vi.fn()

vi.mock('@/services/v3/usage', () => ({
  getUsageSummary: (...args: unknown[]) => getUsageSummary(...args),
}))

vi.mock('@/services/v3/projects', () => ({
  listProjects: (...args: unknown[]) => listProjects(...args),
}))

vi.mock('@/services/v3/system', () => ({
  getSystemConfig: (...args: unknown[]) => getSystemConfig(...args),
}))

vi.mock('@/utils/loadEcharts', () => ({
  loadEcharts: () =>
    Promise.resolve({
      init: () => ({
        setOption: vi.fn(),
        dispose: vi.fn(),
        resize: vi.fn(),
      }),
    }),
}))

function makeProject(overrides: Partial<ProjectSummary> = {}): ProjectSummary {
  return {
    id: overrides.id ?? '11111111-1111-1111-1111-111111111111',
    title: overrides.title ?? '示例项目',
    entry_type: overrides.entry_type ?? 'original',
    stage: overrides.stage ?? 'topic',
    updated_at: overrides.updated_at ?? '2026-07-23T00:00:00Z',
  }
}

function makeSummary(overrides: Partial<UsageSummary> = {}): UsageSummary {
  return {
    timezone: 'Asia/Shanghai',
    date_from: overrides.date_from ?? '2026-06-23',
    date_to: overrides.date_to ?? '2026-07-23',
    group_by: overrides.group_by ?? 'day',
    rows: overrides.rows ?? [
      {
        key: '2026-07-22',
        prompt_tokens: 100,
        completion_tokens: 50,
        total_tokens: 150,
        call_count: 2,
        success_count: 2,
        estimated_cost: '1.25',
        unpriced_call_count: 0,
      },
      {
        key: '2026-07-23',
        prompt_tokens: 10,
        completion_tokens: 5,
        total_tokens: 15,
        call_count: 1,
        success_count: 0,
        estimated_cost: null as unknown as string,
        unpriced_call_count: 1,
      },
    ],
    totals: overrides.totals ?? {
      prompt_tokens: 110,
      completion_tokens: 55,
      total_tokens: 165,
      call_count: 3,
      success_count: 2,
      estimated_cost: '1.25',
      unpriced_call_count: 1,
    },
  }
}

function makeSystemConfig(
  overrides: Partial<SystemConfigState> = {},
): SystemConfigState {
  return {
    revision: overrides.revision ?? 0,
    overlay: overrides.overlay ?? {},
    effective: overrides.effective ?? {
      target_platform: 'generic',
      scoring_preset: 'standard',
      pass_threshold: 75,
      platform_label_zh: '通用',
      daily_cost_alert_cny: null,
    },
  }
}

function renderUsage() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/usage']}>
        <Routes>
          <Route path="/usage" element={<UsagePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('UsagePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listProjects.mockResolvedValue([makeProject()])
    getUsageSummary.mockResolvedValue(makeSummary())
    getSystemConfig.mockResolvedValue(makeSystemConfig())
  })

  it('renders Chinese title, filters, table and chart containers', async () => {
    renderUsage()

    expect(await screen.findByRole('heading', { name: '用量' })).toBeInTheDocument()
    expect(screen.getByLabelText('项目')).toBeInTheDocument()
    expect(screen.getByLabelText('开始日期')).toBeInTheDocument()
    expect(screen.getByLabelText('结束日期')).toBeInTheDocument()
    expect(screen.getByLabelText('分组')).toBeInTheDocument()
    expect(screen.getByTestId('usage-chart-trend')).toBeInTheDocument()
    expect(screen.getByTestId('usage-chart-by-model')).toBeInTheDocument()

    const table = await screen.findByRole('table')
    expect(within(table).getByText('2026-07-22')).toBeInTheDocument()
    expect(within(table).getByText('合计')).toBeInTheDocument()
    expect(within(table).getAllByText('1.25').length).toBeGreaterThanOrEqual(1)
    expect(within(table).getByText('未定价')).toBeInTheDocument()

    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/score-script/i)).not.toBeInTheDocument()
  })

  it('loads summary with live=0 by default', async () => {
    renderUsage()

    await waitFor(() => {
      expect(getUsageSummary).toHaveBeenCalled()
    })

    const calls = getUsageSummary.mock.calls.map((call) => call[0] as Record<string, unknown>)
    expect(calls.length).toBeGreaterThan(0)
    for (const query of calls) {
      expect(query.live).toBe(0)
    }
  })

  it('applies project, date and group_by filters', async () => {
    const user = userEvent.setup()
    const project = makeProject({ title: '过滤项目' })
    listProjects.mockResolvedValue([project])
    getUsageSummary.mockResolvedValue(makeSummary({ group_by: 'model' }))

    renderUsage()

    await screen.findByRole('heading', { name: '用量' })
    await screen.findByRole('option', { name: '过滤项目' })

    await user.selectOptions(screen.getByLabelText('项目'), project.id)

    const dateFrom = screen.getByLabelText('开始日期')
    const dateTo = screen.getByLabelText('结束日期')
    await user.clear(dateFrom)
    await user.type(dateFrom, '2026-07-01')
    await user.clear(dateTo)
    await user.type(dateTo, '2026-07-20')
    await user.selectOptions(screen.getByLabelText('分组'), 'model')

    await waitFor(() => {
      expect(getUsageSummary).toHaveBeenCalledWith(
        expect.objectContaining({
          project_id: project.id,
          date_from: '2026-07-01',
          date_to: '2026-07-20',
          group_by: 'model',
          live: 0,
        }),
      )
    })
  })

  it('shows unpriced label when estimated_cost is null', async () => {
    getUsageSummary.mockResolvedValue(
      makeSummary({
        rows: [
          {
            key: 'gpt-unpriced',
            prompt_tokens: 1,
            completion_tokens: 1,
            total_tokens: 2,
            call_count: 1,
            success_count: 1,
            estimated_cost: null as unknown as string,
            unpriced_call_count: 1,
          },
        ],
        totals: {
          prompt_tokens: 1,
          completion_tokens: 1,
          total_tokens: 2,
          call_count: 1,
          success_count: 1,
          estimated_cost: null as unknown as string,
          unpriced_call_count: 1,
        },
        group_by: 'model',
      }),
    )

    renderUsage()

    const table = await screen.findByRole('table')
    expect(within(table).getAllByText('未定价').length).toBeGreaterThanOrEqual(1)
  })

  it('shows load error in Chinese', async () => {
    getUsageSummary.mockRejectedValue(new Error('用量加载失败'))

    renderUsage()

    expect(await screen.findByText(/用量加载失败/)).toBeInTheDocument()
  })

  it('shows cost alert banner and tints today row when over threshold', async () => {
    const today = getShanghaiDateString()
    getSystemConfig.mockResolvedValue(
      makeSystemConfig({
        overlay: { daily_cost_alert_cny: 5 },
        effective: {
          target_platform: 'generic',
          scoring_preset: 'standard',
          pass_threshold: 75,
          platform_label_zh: '通用',
          daily_cost_alert_cny: 5,
        },
      }),
    )
    getUsageSummary.mockResolvedValue(
      makeSummary({
        date_from: today,
        date_to: today,
        rows: [
          {
            key: today,
            prompt_tokens: 100,
            completion_tokens: 50,
            total_tokens: 150,
            call_count: 2,
            success_count: 2,
            estimated_cost: '12.5',
            unpriced_call_count: 0,
          },
        ],
        totals: {
          prompt_tokens: 100,
          completion_tokens: 50,
          total_tokens: 150,
          call_count: 2,
          success_count: 2,
          estimated_cost: '12.5',
          unpriced_call_count: 0,
        },
      }),
    )

    renderUsage()

    expect(await screen.findByTestId('daily-cost-alert-banner')).toHaveTextContent(
      /已超过预警阈值/,
    )
    const table = await screen.findByRole('table')
    const todayCell = within(table).getByText(today)
    expect(todayCell.closest('tr')).toHaveAttribute('data-over-alert', 'true')
  })

  it('hides cost alert banner when under threshold', async () => {
    const today = getShanghaiDateString()
    getSystemConfig.mockResolvedValue(
      makeSystemConfig({
        effective: {
          target_platform: 'generic',
          scoring_preset: 'standard',
          pass_threshold: 75,
          platform_label_zh: '通用',
          daily_cost_alert_cny: 100,
        },
      }),
    )
    getUsageSummary.mockResolvedValue(
      makeSummary({
        rows: [
          {
            key: today,
            prompt_tokens: 10,
            completion_tokens: 5,
            total_tokens: 15,
            call_count: 1,
            success_count: 1,
            estimated_cost: '1',
            unpriced_call_count: 0,
          },
        ],
        totals: {
          prompt_tokens: 10,
          completion_tokens: 5,
          total_tokens: 15,
          call_count: 1,
          success_count: 1,
          estimated_cost: '1',
          unpriced_call_count: 0,
        },
      }),
    )

    renderUsage()

    await screen.findByRole('table')
    expect(screen.queryByTestId('daily-cost-alert-banner')).not.toBeInTheDocument()
  })
})
