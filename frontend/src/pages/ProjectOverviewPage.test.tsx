import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ArtifactVersion, ProjectSummary } from '@/types/v3/domain'
import { ProjectOverviewPage } from './ProjectOverviewPage'

const getProject = vi.fn()
const archiveProject = vi.fn()
const deleteProject = vi.fn()
const listArtifactVersions = vi.fn()
const rollbackArtifact = vi.fn()

vi.mock('@/services/v3/projects', () => ({
  getProject: (...args: unknown[]) => getProject(...args),
  archiveProject: (...args: unknown[]) => archiveProject(...args),
  deleteProject: (...args: unknown[]) => deleteProject(...args),
}))

vi.mock('@/services/v3/artifacts', () => ({
  listArtifactVersions: (...args: unknown[]) => listArtifactVersions(...args),
  rollbackArtifact: (...args: unknown[]) => rollbackArtifact(...args),
}))

const sampleProject: ProjectSummary = {
  id: 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',
  title: '重生之逆袭人生',
  entry_type: 'original',
  stage: 'topic',
  progress_percent: 12,
  archived_at: null,
  updated_at: '2026-07-23T08:00:00Z',
}

function makeVersion(version: number, status: ArtifactVersion['status']): ArtifactVersion {
  return {
    id: `bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeee${String(version).padStart(2, '0')}`,
    artifact_key: 'project_brief',
    version,
    schema_version: 1,
    status,
    payload: { title: `v${version}` },
    created_at: '2026-07-23T08:00:00Z',
  }
}

function renderOverview(projectId = sampleProject.id) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/settings`]}>
        <Routes>
          <Route path="/projects/:id/settings" element={<ProjectOverviewPage />} />
          <Route path="/projects/:id/topic" element={<div>选题定调占位</div>} />
          <Route path="/projects/:id/blueprint" element={<div>故事蓝图占位</div>} />
          <Route path="/projects/:id/episodes" element={<div>分集规划占位</div>} />
          <Route path="/projects/:id/editor" element={<div>正文编辑占位</div>} />
          <Route path="/projects/:id/quality" element={<div>质检中心占位</div>} />
          <Route path="/projects/:id/delivery" element={<div>交付中心占位</div>} />
          <Route path="/dashboard" element={<div>仪表盘</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectOverviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listArtifactVersions.mockResolvedValue({ items: [] })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  it('loads project and shows title, entry, stage, progress', async () => {
    getProject.mockResolvedValue(sampleProject)

    renderOverview()

    expect(await screen.findByRole('heading', { name: '重生之逆袭人生' })).toBeInTheDocument()
    expect(screen.getByText('原创')).toBeInTheDocument()
    expect(screen.getByText('选题定调')).toBeInTheDocument()
    expect(screen.getByText('12%')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '去选题定调' })).toBeInTheDocument()
    expect(getProject).toHaveBeenCalledWith(sampleProject.id)
  })

  it('navigates to topic placeholder via CTA', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue(sampleProject)

    renderOverview()

    await screen.findByText('重生之逆袭人生')
    await user.click(screen.getByRole('link', { name: '去选题定调' }))

    expect(await screen.findByText('选题定调占位')).toBeInTheDocument()
  })

  it('shows blueprint CTA when stage is blueprint', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue({
      ...sampleProject,
      stage: 'blueprint',
    })

    renderOverview()

    await screen.findByText('重生之逆袭人生')
    expect(screen.getByRole('link', { name: '去故事蓝图' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '去选题定调' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: '去故事蓝图' }))
    expect(await screen.findByText('故事蓝图占位')).toBeInTheDocument()
  })

  it('shows episodes CTA when stage is episodes', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue({
      ...sampleProject,
      stage: 'episodes',
    })

    renderOverview()

    await screen.findByText('重生之逆袭人生')
    const link = screen.getByRole('link', { name: '去分集规划' })
    expect(link).toHaveAttribute('href', `/projects/${sampleProject.id}/episodes`)
    await user.click(link)
    expect(await screen.findByText('分集规划占位')).toBeInTheDocument()
  })

  it('shows editor CTA when stage is writing', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue({
      ...sampleProject,
      stage: 'writing',
    })

    renderOverview()

    await screen.findByText('重生之逆袭人生')
    const link = screen.getByRole('link', { name: '去正文编辑' })
    expect(link).toHaveAttribute('href', `/projects/${sampleProject.id}/editor`)
    await user.click(link)
    expect(await screen.findByText('正文编辑占位')).toBeInTheDocument()
  })

  it('shows quality CTA when stage is quality', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue({
      ...sampleProject,
      stage: 'quality',
    })

    renderOverview()

    await screen.findByText('重生之逆袭人生')
    const link = screen.getByRole('link', { name: '去质检中心' })
    expect(link).toHaveAttribute('href', `/projects/${sampleProject.id}/quality`)
    expect(screen.queryByText('后续开放')).not.toBeInTheDocument()
    await user.click(link)
    expect(await screen.findByText('质检中心占位')).toBeInTheDocument()
  })

  it('shows delivery CTA when stage is delivery', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue({
      ...sampleProject,
      stage: 'delivery',
    })

    renderOverview()

    await screen.findByText('重生之逆袭人生')
    const link = screen.getByRole('link', { name: '去交付中心' })
    expect(link).toHaveAttribute('href', `/projects/${sampleProject.id}/delivery`)
    expect(screen.queryByText('后续开放')).not.toBeInTheDocument()
    await user.click(link)
    expect(await screen.findByText('交付中心占位')).toBeInTheDocument()
  })

  it('hides archive button when project is already archived', async () => {
    getProject.mockResolvedValue({
      ...sampleProject,
      archived_at: '2026-07-23T09:00:00Z',
    })

    renderOverview()

    await screen.findByText('重生之逆袭人生')
    expect(screen.getByText('该项目已归档。')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '归档项目' })).not.toBeInTheDocument()
  })

  it('archives with confirm then navigates to dashboard', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue(sampleProject)
    archiveProject.mockResolvedValue({
      ...sampleProject,
      archived_at: '2026-07-23T09:00:00Z',
    })

    renderOverview()

    await screen.findByText('重生之逆袭人生')
    await user.click(screen.getByRole('button', { name: '归档项目' }))

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent(/确认归档/)
    await user.click(screen.getByRole('button', { name: '确认归档' }))

    await waitFor(() => {
      expect(archiveProject).toHaveBeenCalledWith(sampleProject.id)
    })

    expect(await screen.findByText('仪表盘')).toBeInTheDocument()
  })

  it('deletes with confirm then navigates to dashboard', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue(sampleProject)
    deleteProject.mockResolvedValue({ deleted: true, id: sampleProject.id })

    renderOverview()

    await screen.findByText('重生之逆袭人生')
    await user.click(screen.getByRole('button', { name: '删除项目' }))

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent(/确认删除/)
    await user.click(screen.getByRole('button', { name: '确认删除' }))

    await waitFor(() => {
      expect(deleteProject).toHaveBeenCalledWith(sampleProject.id)
    })

    expect(await screen.findByText('仪表盘')).toBeInTheDocument()
  })

  it('lists artifact versions and confirms rollback', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue(sampleProject)
    listArtifactVersions.mockResolvedValue({
      items: [makeVersion(2, 'committed'), makeVersion(1, 'superseded')],
    })
    rollbackArtifact.mockResolvedValue(makeVersion(3, 'committed'))

    renderOverview()

    expect(await screen.findByRole('heading', { name: '版本回滚' })).toBeInTheDocument()
    await waitFor(() => {
      expect(listArtifactVersions).toHaveBeenCalledWith(sampleProject.id, 'project_brief')
    })

    const list = await screen.findByRole('list', { name: '版本列表' })
    expect(within(list).getByText(/v2/)).toBeInTheDocument()
    expect(within(list).getByText(/v1/)).toBeInTheDocument()

    const radios = within(list).getAllByRole('radio')
    await user.click(radios[1])
    await user.click(screen.getByRole('button', { name: '确认回滚' }))

    await waitFor(() => {
      expect(rollbackArtifact).toHaveBeenCalledWith(sampleProject.id, {
        artifact_key: 'project_brief',
        source_version: 1,
      })
    })
    expect(await screen.findByText(/已回滚为新版本 v3/)).toBeInTheDocument()
  })

  it('reloads versions when artifact key changes', async () => {
    const user = userEvent.setup()
    getProject.mockResolvedValue(sampleProject)
    listArtifactVersions
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValueOnce({
        items: [makeVersion(1, 'committed')],
      })

    renderOverview()
    await screen.findByRole('heading', { name: '版本回滚' })
    await waitFor(() => {
      expect(listArtifactVersions).toHaveBeenCalledWith(sampleProject.id, 'project_brief')
    })

    await user.selectOptions(screen.getByLabelText('产物类型'), 'episode_plan')

    await waitFor(() => {
      expect(listArtifactVersions).toHaveBeenCalledWith(sampleProject.id, 'episode_plan')
    })
  })
})
