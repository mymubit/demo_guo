import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ProjectSummary } from '@/types/v3/domain'
import {
  ProjectStageRedirect,
  ProjectWorkbenchLayout,
} from './ProjectWorkbenchLayout'

const getProject = vi.fn()

vi.mock('@/services/v3/projects', () => ({
  getProject: (...args: unknown[]) => getProject(...args),
}))

const PROJECT_ID = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'

function makeProject(overrides: Partial<ProjectSummary> = {}): ProjectSummary {
  return {
    id: PROJECT_ID,
    title: overrides.title ?? '向导项目',
    entry_type: overrides.entry_type ?? 'original',
    stage: overrides.stage ?? 'blueprint',
    progress_percent: overrides.progress_percent ?? 20,
    archived_at: overrides.archived_at ?? null,
    updated_at: overrides.updated_at ?? '2026-07-24T00:00:00Z',
  }
}

function renderWorkbench(path: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectWorkbenchLayout />}>
            <Route index element={<ProjectStageRedirect />} />
            <Route path="settings" element={<div>设置页</div>} />
            <Route path="topic" element={<div>选题页</div>} />
            <Route path="blueprint" element={<div>蓝图页</div>} />
            <Route path="episodes" element={<div>分集页</div>} />
            <Route path="editor" element={<div>正文页</div>} />
            <Route path="quality" element={<div>质检页</div>} />
            <Route path="delivery" element={<div>交付页</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectWorkbenchLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders stage rail and opens current stage content', async () => {
    getProject.mockResolvedValue(makeProject({ stage: 'blueprint' }))
    renderWorkbench(`/projects/${PROJECT_ID}/blueprint`)

    expect(await screen.findByRole('navigation', { name: '创作阶段' })).toBeInTheDocument()
    expect(screen.getByText('向导项目')).toBeInTheDocument()
    expect(screen.getByText('蓝图页')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /故事蓝图/ })).toHaveAttribute(
      'href',
      `/projects/${PROJECT_ID}/blueprint`,
    )
  })

  it('index redirects to path for project.stage', async () => {
    getProject.mockResolvedValue(makeProject({ stage: 'episodes' }))
    renderWorkbench(`/projects/${PROJECT_ID}`)

    expect(await screen.findByText('分集页')).toBeInTheDocument()
  })

  it('next/prev buttons navigate adjacent stages', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue(makeProject({ stage: 'blueprint' }))
    renderWorkbench(`/projects/${PROJECT_ID}/blueprint`)

    await screen.findByText('蓝图页')
    await user.click(screen.getByRole('button', { name: '下一步' }))
    expect(await screen.findByText('分集页')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '上一步' }))
    expect(await screen.findByText('蓝图页')).toBeInTheDocument()
  })

  it('settings link goes to project settings', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue(makeProject())
    renderWorkbench(`/projects/${PROJECT_ID}/topic`)

    await screen.findByText('选题页')
    await user.click(screen.getByRole('link', { name: '项目设置与回滚' }))
    expect(await screen.findByText('设置页')).toBeInTheDocument()
  })

  it('shows load error with back to dashboard', async () => {
    getProject.mockRejectedValue(new Error('项目不存在'))
    renderWorkbench(`/projects/${PROJECT_ID}/topic`)

    expect(await screen.findByText(/项目不存在|加载失败|请求失败/)).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '返回仪表盘' })).toBeInTheDocument()
    })
  })
})
