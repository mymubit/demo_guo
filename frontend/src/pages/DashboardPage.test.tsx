import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ProjectSummary, SystemConfigState, UsageSummary } from '@/types/v3/domain'
import { getShanghaiDateString } from '@/utils/dailyCostAlert'
import { DashboardPage } from './DashboardPage'

const listProjects = vi.fn()
const createProject = vi.fn()
const archiveProject = vi.fn()
const deleteProject = vi.fn()
const getSystemConfig = vi.fn()
const getUsageSummary = vi.fn()

vi.mock('@/services/v3/projects', () => ({
  listProjects: (...args: unknown[]) => listProjects(...args),
  createProject: (...args: unknown[]) => createProject(...args),
  archiveProject: (...args: unknown[]) => archiveProject(...args),
  deleteProject: (...args: unknown[]) => deleteProject(...args),
}))

vi.mock('@/services/v3/system', () => ({
  getSystemConfig: (...args: unknown[]) => getSystemConfig(...args),
}))

vi.mock('@/services/v3/usage', () => ({
  getUsageSummary: (...args: unknown[]) => getUsageSummary(...args),
}))

const sampleProject: ProjectSummary = {
  id: 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',
  title: '重生之逆袭人生',
  entry_type: 'original',
  stage: 'topic',
  progress_percent: 0,
  archived_at: null,
  updated_at: '2026-07-23T08:00:00Z',
}

const blueprintProject: ProjectSummary = {
  id: 'bbbbbbbb-cccc-4ddd-8eee-ffffffffffff',
  title: '都市爱情短剧',
  entry_type: 'adapt',
  stage: 'blueprint',
  progress_percent: 20,
  archived_at: null,
  updated_at: '2026-07-23T09:00:00Z',
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

function makeTodayUsage(cost: string): UsageSummary {
  const today = getShanghaiDateString()
  return {
    timezone: 'Asia/Shanghai',
    date_from: today,
    date_to: today,
    group_by: 'day',
    rows: [
      {
        key: today,
        prompt_tokens: 10,
        completion_tokens: 5,
        total_tokens: 15,
        call_count: 1,
        success_count: 1,
        estimated_cost: cost,
        unpriced_call_count: 0,
      },
    ],
    totals: {
      prompt_tokens: 10,
      completion_tokens: 5,
      total_tokens: 15,
      call_count: 1,
      success_count: 1,
      estimated_cost: cost,
      unpriced_call_count: 0,
    },
  }
}

function renderDashboard() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/projects/:id/topic" element={<div>选题定调占位</div>} />
          <Route path="/projects/:id/blueprint" element={<div>故事蓝图占位</div>} />
          <Route path="/projects/:id" element={<div>项目概览占位</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getSystemConfig.mockResolvedValue(makeSystemConfig())
    getUsageSummary.mockResolvedValue(makeTodayUsage('0'))
  })

  it('renders project titles from listProjects', async () => {
    listProjects.mockResolvedValue([sampleProject])

    renderDashboard()

    expect(await screen.findByText('重生之逆袭人生')).toBeInTheDocument()
    expect(screen.getByText(/原创\s*·\s*选题定调/)).toBeInTheDocument()
    expect(screen.queryByText(sampleProject.id)).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: /重生之逆袭人生/ })).toHaveAttribute(
      'href',
      `/projects/${sampleProject.id}/topic`,
    )
  })

  it('board/list card for blueprint stage links to blueprint path', async () => {
    listProjects.mockResolvedValue([blueprintProject])

    renderDashboard()

    expect(await screen.findByText('都市爱情短剧')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /都市爱情短剧/ })).toHaveAttribute(
      'href',
      `/projects/${blueprintProject.id}/blueprint`,
    )
  })

  it('shows empty state when there are no projects', async () => {
    listProjects.mockResolvedValue([])

    renderDashboard()

    expect(await screen.findByText(/还没有项目/)).toBeInTheDocument()
  })

  it('creates a project via dialog and navigates to topic workbench', async () => {
    const user = userEvent.setup()
    listProjects.mockResolvedValue([])
    createProject.mockResolvedValue({
      ...sampleProject,
      id: '11111111-2222-4333-8444-555555555555',
      title: '新剧标题',
      entry_type: 'adapt',
    })

    renderDashboard()

    await screen.findByText(/还没有项目/)
    await user.click(screen.getByRole('button', { name: '新建项目' }))

    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByLabelText('项目标题'), '新剧标题')
    await user.selectOptions(within(dialog).getByLabelText('创作来源'), 'adapt')
    await user.click(within(dialog).getByRole('button', { name: '创建并进入' }))

    await waitFor(() => {
      expect(createProject).toHaveBeenCalledWith({
        title: '新剧标题',
        entry_type: 'adapt',
      })
    })

    expect(await screen.findByText('选题定调占位')).toBeInTheDocument()
  })

  it('toggles include archived and calls listProjects(true)', async () => {
    const user = userEvent.setup()
    listProjects.mockResolvedValue([sampleProject])

    renderDashboard()

    await screen.findByText('重生之逆袭人生')
    expect(listProjects).toHaveBeenCalledWith()

    await user.click(screen.getByRole('checkbox', { name: '显示已归档' }))

    await waitFor(() => {
      expect(listProjects).toHaveBeenCalledWith(true)
    })
  })

  it('archives a project from card after confirm', async () => {
    const user = userEvent.setup()
    listProjects.mockResolvedValue([sampleProject])
    archiveProject.mockResolvedValue({
      ...sampleProject,
      archived_at: '2026-07-23T09:00:00Z',
    })

    renderDashboard()

    await screen.findByText('重生之逆袭人生')
    await user.click(screen.getByRole('button', { name: '归档' }))

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent(/确认归档/)
    await user.click(screen.getByRole('button', { name: '确认归档' }))

    await waitFor(() => {
      expect(archiveProject).toHaveBeenCalledWith(sampleProject.id)
    })
  })

  it('deletes a project from card after confirm', async () => {
    const user = userEvent.setup()
    listProjects.mockResolvedValue([sampleProject])
    deleteProject.mockResolvedValue({ deleted: true, id: sampleProject.id })

    renderDashboard()

    await screen.findByText('重生之逆袭人生')
    await user.click(screen.getByRole('button', { name: '删除' }))

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent(/确认删除/)
    await user.click(screen.getByRole('button', { name: '确认删除' }))

    await waitFor(() => {
      expect(deleteProject).toHaveBeenCalledWith(sampleProject.id)
    })
  })

  it('shows daily cost alert banner when today cost exceeds threshold', async () => {
    listProjects.mockResolvedValue([sampleProject])
    getSystemConfig.mockResolvedValue(
      makeSystemConfig({
        effective: {
          target_platform: 'generic',
          scoring_preset: 'standard',
          pass_threshold: 75,
          platform_label_zh: '通用',
          daily_cost_alert_cny: 5,
        },
      }),
    )
    getUsageSummary.mockResolvedValue(makeTodayUsage('9.99'))

    renderDashboard()

    expect(await screen.findByTestId('daily-cost-alert-banner')).toHaveTextContent(
      /已超过预警阈值/,
    )
  })

  it('hides daily cost alert banner when threshold unset', async () => {
    listProjects.mockResolvedValue([sampleProject])
    getSystemConfig.mockResolvedValue(makeSystemConfig())
    getUsageSummary.mockResolvedValue(makeTodayUsage('99'))

    renderDashboard()

    await screen.findByText('重生之逆袭人生')
    expect(screen.queryByTestId('daily-cost-alert-banner')).not.toBeInTheDocument()
  })

  it('filters projects by title search case-insensitively', async () => {
    const user = userEvent.setup()
    listProjects.mockResolvedValue([sampleProject, blueprintProject])

    renderDashboard()

    await screen.findByText('重生之逆袭人生')
    expect(screen.getByText('都市爱情短剧')).toBeInTheDocument()

    await user.type(screen.getByRole('searchbox'), '都市')

    expect(screen.queryByText('重生之逆袭人生')).not.toBeInTheDocument()
    expect(screen.getByText('都市爱情短剧')).toBeInTheDocument()
  })

  it('shows filter empty state when search has no matches', async () => {
    const user = userEvent.setup()
    listProjects.mockResolvedValue([sampleProject])

    renderDashboard()

    await screen.findByText('重生之逆袭人生')
    await user.type(screen.getByRole('searchbox'), '不存在的关键词')

    expect(await screen.findByText(/没有匹配的项目/)).toBeInTheDocument()
    expect(screen.queryByText('重生之逆袭人生')).not.toBeInTheDocument()
  })

  it('switches to board view and groups projects by stage columns', async () => {
    const user = userEvent.setup()
    listProjects.mockResolvedValue([sampleProject, blueprintProject])

    renderDashboard()

    await screen.findByText('重生之逆袭人生')
    await user.click(screen.getByRole('button', { name: '看板' }))

    expect(screen.getByRole('region', { name: '选题定调' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: '故事蓝图' })).toBeInTheDocument()

    const topicColumn = screen.getByRole('region', { name: '选题定调' })
    const blueprintColumn = screen.getByRole('region', { name: '故事蓝图' })

    expect(within(topicColumn).getByText('重生之逆袭人生')).toBeInTheDocument()
    expect(within(blueprintColumn).getByText('都市爱情短剧')).toBeInTheDocument()
    expect(within(blueprintColumn).queryByText('重生之逆袭人生')).not.toBeInTheDocument()
  })

  it('clears search from filter empty state', async () => {
    const user = userEvent.setup()
    listProjects.mockResolvedValue([sampleProject])

    renderDashboard()

    await screen.findByText('重生之逆袭人生')
    await user.type(screen.getByRole('searchbox'), 'zzz')
    await user.click(await screen.findByRole('button', { name: '清除筛选' }))

    expect(await screen.findByText('重生之逆袭人生')).toBeInTheDocument()
    expect(screen.getByRole('searchbox')).toHaveValue('')
  })
})