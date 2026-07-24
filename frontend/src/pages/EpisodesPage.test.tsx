import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ArtifactVersion, BlueprintState, EpisodesState } from '@/types/v3/domain'
import { EpisodesPage } from './EpisodesPage'

const getEpisodesState = vi.fn()
const generateEpisodePlan = vi.fn()
const confirmEpisodePlan = vi.fn()
const reviseEpisodePlan = vi.fn()
const getBlueprintState = vi.fn()

vi.mock('@/services/v3/episodes', () => ({
  getEpisodesState: (...args: unknown[]) => getEpisodesState(...args),
  generateEpisodePlan: (...args: unknown[]) => generateEpisodePlan(...args),
  confirmEpisodePlan: (...args: unknown[]) => confirmEpisodePlan(...args),
  reviseEpisodePlan: (...args: unknown[]) => reviseEpisodePlan(...args),
}))

vi.mock('@/services/v3/blueprint', () => ({
  getBlueprintState: (...args: unknown[]) => getBlueprintState(...args),
}))

const PROJECT_ID = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'

function makeArtifact(
  key: string,
  overrides: Partial<ArtifactVersion> & Pick<ArtifactVersion, 'status' | 'payload'>,
): ArtifactVersion {
  return {
    id: overrides.id ?? '11111111-1111-4111-8111-111111111111',
    artifact_key: key,
    version: overrides.version ?? 1,
    schema_version: 1,
    status: overrides.status,
    payload: overrides.payload,
    created_at: overrides.created_at ?? '2026-07-23T08:00:00Z',
  }
}

function emptyEpisodes(overrides: Partial<EpisodesState> = {}): EpisodesState {
  return {
    stage: 'episodes',
    committed: null,
    candidate: null,
    latest_run: null,
    ...overrides,
  }
}

function blueprintWithCommitted(committed = true): BlueprintState {
  return {
    committed: committed
      ? {
          story_bible: makeArtifact('story_bible', {
            status: 'committed',
            payload: { title: '已确认蓝图' },
          }),
        }
      : null,
    candidate: null,
    latest_run: null,
  }
}

function episodePlanPayload(episodes: Array<Record<string, unknown>>) {
  return { episodes }
}

function renderEpisodes(projectId = PROJECT_ID) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/episodes`]}>
        <Routes>
          <Route path="/projects/:id/episodes" element={<EpisodesPage />} />
          <Route path="/projects/:id/blueprint" element={<div>故事蓝图占位</div>} />
          <Route path="/projects/:id" element={<div>项目概览占位</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('EpisodesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Chinese UI without operation recipe ids', async () => {
    getBlueprintState.mockResolvedValue(blueprintWithCommitted(true))
    getEpisodesState.mockResolvedValue(emptyEpisodes())

    renderEpisodes()

    expect(await screen.findByRole('heading', { name: '分集规划' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成全剧规划' })).toBeInTheDocument()
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/design-episode-plan/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/generate_episode_plan/i)).not.toBeInTheDocument()
  })

  it('disables generate without committed blueprint and shows dependency hint', async () => {
    getBlueprintState.mockResolvedValue(blueprintWithCommitted(false))
    getEpisodesState.mockResolvedValue(emptyEpisodes())

    renderEpisodes()

    expect(await screen.findByText(/请先确认故事蓝图/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成全剧规划' })).toBeDisabled()
    expect(screen.getByRole('link', { name: '去故事蓝图' })).toBeInTheDocument()
  })

  it('calls generateEpisodePlan when generate is clicked with committed blueprint', async () => {
    const user = userEvent.setup()
    getBlueprintState.mockResolvedValue(blueprintWithCommitted(true))
    getEpisodesState.mockResolvedValue(emptyEpisodes())
    generateEpisodePlan.mockResolvedValue({
      command_run: {
        id: '22222222-2222-4222-8222-222222222222',
        command_type: 'generate_episode_plan',
        status: 'queued',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:01:00Z',
        updated_at: '2026-07-23T08:01:00Z',
      },
    })

    renderEpisodes()

    expect(await screen.findByText(/尚未生成分集规划/)).toBeInTheDocument()
    const generateButton = screen.getByRole('button', { name: '生成全剧规划' })
    expect(generateButton).toBeEnabled()
    await user.click(generateButton)

    await waitFor(() => {
      expect(generateEpisodePlan).toHaveBeenCalledWith(PROJECT_ID)
    })
  })

  it('shows episode title, hook and emotion then confirms candidate', async () => {
    const user = userEvent.setup()
    getBlueprintState.mockResolvedValue(blueprintWithCommitted(true))
    getEpisodesState.mockResolvedValue(
      emptyEpisodes({
        candidate: makeArtifact('episode_plan', {
          status: 'candidate',
          payload: episodePlanPayload([
            {
              episode: 1,
              title: '重生归来',
              opening_hook: '闹钟响起她回到被抛弃当天',
              ending_hook: '她发现授权书日期与记忆不符',
              emotion_nodes: {
                EV: { emotion: '震惊', event: '发现授权书日期异常' },
              },
            },
          ]),
        }),
        latest_run: {
          id: '33333333-3333-4333-8333-333333333333',
          command_type: 'generate_episode_plan',
          status: 'succeeded',
          project_id: PROJECT_ID,
          error_message: '',
          result_payload: {},
          created_at: '2026-07-23T08:02:00Z',
          updated_at: '2026-07-23T08:02:00Z',
        },
      }),
    )
    confirmEpisodePlan.mockResolvedValue({
      command_run: {
        id: '44444444-4444-4444-8444-444444444444',
        command_type: 'confirm_episode_plan',
        status: 'succeeded',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:03:00Z',
        updated_at: '2026-07-23T08:03:00Z',
      },
    })

    renderEpisodes()

    expect((await screen.findAllByText('重生归来')).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('闹钟响起她回到被抛弃当天').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('震惊').length).toBeGreaterThanOrEqual(1)
    await user.click(screen.getByRole('button', { name: '确认采用' }))

    await waitFor(() => {
      expect(confirmEpisodePlan).toHaveBeenCalledWith(PROJECT_ID)
    })
  })

  it('revises selected episodes via multi-select', async () => {
    const user = userEvent.setup()
    getBlueprintState.mockResolvedValue(blueprintWithCommitted(true))
    getEpisodesState.mockResolvedValue(
      emptyEpisodes({
        stage: 'writing',
        committed: makeArtifact('episode_plan', {
          status: 'committed',
          payload: episodePlanPayload([
            { episode: 1, title: '第一集', ending_hook: '钩子甲' },
            { episode: 2, title: '第二集', ending_hook: '钩子乙' },
          ]),
        }),
      }),
    )
    reviseEpisodePlan.mockResolvedValue({
      command_run: {
        id: '55555555-5555-4555-8555-555555555555',
        command_type: 'revise_episode_plan',
        status: 'queued',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:04:00Z',
        updated_at: '2026-07-23T08:04:00Z',
      },
    })

    renderEpisodes()

    expect((await screen.findAllByText('第一集')).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByRole('button', { name: '局部修订' })).toBeDisabled()

    await user.click(screen.getByRole('checkbox', { name: /第 2 集/ }))
    expect(screen.getByRole('button', { name: '局部修订' })).toBeEnabled()
    await user.click(screen.getByRole('button', { name: '局部修订' }))

    await waitFor(() => {
      expect(reviseEpisodePlan).toHaveBeenCalledWith(PROJECT_ID, { episode_numbers: [2] })
    })
  })

  it('shows in-progress run status and disables generate', async () => {
    getBlueprintState.mockResolvedValue(blueprintWithCommitted(true))
    getEpisodesState.mockResolvedValue(
      emptyEpisodes({
        latest_run: {
          id: '66666666-6666-4666-8666-666666666666',
          command_type: 'generate_episode_plan',
          status: 'running',
          project_id: PROJECT_ID,
          error_message: '',
          result_payload: {},
          created_at: '2026-07-23T08:05:00Z',
          updated_at: '2026-07-23T08:05:00Z',
        },
      }),
    )

    renderEpisodes()

    expect(await screen.findByText(/最近任务：进行中/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成全剧规划' })).toBeDisabled()
  })
})
