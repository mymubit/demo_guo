import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { ArtifactVersion, EpisodesState, ScriptsState } from '@/types/v3/domain'
import { ScriptEditorPage } from './ScriptEditorPage'

const getScriptsState = vi.fn()
const getScriptEpisode = vi.fn()
const putScriptDraft = vi.fn()
const generateScriptBatch = vi.fn()
const confirmScriptCandidate = vi.fn()
const getEpisodesState = vi.fn()

vi.mock('@/services/v3/scripts', () => ({
  getScriptsState: (...args: unknown[]) => getScriptsState(...args),
  getScriptEpisode: (...args: unknown[]) => getScriptEpisode(...args),
  putScriptDraft: (...args: unknown[]) => putScriptDraft(...args),
  generateScriptBatch: (...args: unknown[]) => generateScriptBatch(...args),
  confirmScriptCandidate: (...args: unknown[]) => confirmScriptCandidate(...args),
}))

vi.mock('@/services/v3/episodes', () => ({
  getEpisodesState: (...args: unknown[]) => getEpisodesState(...args),
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

function emptyScripts(overrides: Partial<ScriptsState> = {}): ScriptsState {
  return {
    committed: null,
    candidate: null,
    drafts: [],
    latest_run: null,
    ...overrides,
  }
}

function emptyEpisodes(overrides: Partial<EpisodesState> = {}): EpisodesState {
  return {
    stage: 'writing',
    committed: null,
    candidate: null,
    latest_run: null,
    ...overrides,
  }
}

function episodePlanCommitted(count = 2): EpisodesState {
  return emptyEpisodes({
    committed: makeArtifact('episode_plan', {
      status: 'committed',
      payload: {
        episodes: Array.from({ length: count }, (_, i) => ({
          episode: i + 1,
          title: `第${i + 1}集标题`,
        })),
      },
    }),
  })
}

function renderEditor(path = `/projects/${PROJECT_ID}/editor`) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/projects/:id/editor" element={<ScriptEditorPage />} />
          <Route path="/projects/:id/episodes" element={<div>分集规划占位</div>} />
          <Route path="/projects/:id" element={<div>项目概览占位</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ScriptEditorPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders Chinese UI without operation recipe ids', async () => {
    getEpisodesState.mockResolvedValue(episodePlanCommitted())
    getScriptsState.mockResolvedValue(emptyScripts())
    getScriptEpisode.mockResolvedValue({
      episode_number: 1,
      committed: null,
      candidate: null,
      draft: null,
    })

    renderEditor()

    expect(await screen.findByRole('heading', { name: '正文编辑' })).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /生成本批/ })).toBeInTheDocument()
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/write-episodes/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/write_episode_batch/i)).not.toBeInTheDocument()
  })

  it('disables generate without committed episode plan and links to episodes', async () => {
    getEpisodesState.mockResolvedValue(emptyEpisodes())
    getScriptsState.mockResolvedValue(emptyScripts())
    getScriptEpisode.mockResolvedValue({
      episode_number: 1,
      committed: null,
      candidate: null,
      draft: null,
    })

    renderEditor()

    expect(await screen.findByText(/请先确认分集规划/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /生成本批/ })).toBeDisabled()
    expect(screen.getByRole('link', { name: '去分集规划' })).toBeInTheDocument()
  })

  it('lists episodes with draft and committed completion markers', async () => {
    getEpisodesState.mockResolvedValue(episodePlanCommitted(2))
    getScriptsState.mockResolvedValue(
      emptyScripts({
        drafts: [
          {
            episode_number: 1,
            payload: {
              scenes: [{ id: 's1', heading: 'INT. 咖啡厅', beats: [{ type: 'action', text: '推门' }] }],
            },
            updated_at: '2026-07-23T08:10:00Z',
          },
        ],
        committed: makeArtifact('episode_scripts', {
          status: 'committed',
          payload: {
            episodes: [
              {
                episode_number: 2,
                title: '已确认第二集',
                script: '正文',
                word_count: 100,
                dialogue_ratio: 0.3,
                scene_count: 1,
              },
            ],
          },
        }),
      }),
    )
    getScriptEpisode.mockResolvedValue({
      episode_number: 1,
      committed: null,
      candidate: null,
      draft: {
        episode_number: 1,
        payload: {
          scenes: [{ id: 's1', heading: 'INT. 咖啡厅', beats: [{ type: 'action', text: '推门' }] }],
        },
        updated_at: '2026-07-23T08:10:00Z',
      },
    })

    renderEditor()

    expect(await screen.findByRole('button', { name: /第 1 集/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /第 2 集/ })).toBeInTheDocument()
    expect(screen.getByText('有草稿')).toBeInTheDocument()
    expect(screen.getByText('已确认')).toBeInTheDocument()
    expect(screen.getByDisplayValue('INT. 咖啡厅')).toBeInTheDocument()
  })

  it('autosaves draft after 1s debounce', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

    getEpisodesState.mockResolvedValue(episodePlanCommitted())
    getScriptsState.mockResolvedValue(emptyScripts())
    getScriptEpisode.mockResolvedValue({
      episode_number: 1,
      committed: null,
      candidate: null,
      draft: {
        episode_number: 1,
        payload: {
          scenes: [{ id: 's1', heading: '旧场次', beats: [{ type: 'action', text: '旧动作' }] }],
        },
        updated_at: '2026-07-23T08:00:00Z',
      },
    })
    putScriptDraft.mockResolvedValue({
      episode_number: 1,
      payload: {
        scenes: [{ id: 's1', heading: '新场次', beats: [{ type: 'action', text: '旧动作' }] }],
      },
      updated_at: '2026-07-23T08:20:00Z',
    })

    renderEditor(`/projects/${PROJECT_ID}/editor?ep=1`)

    const heading = await screen.findByDisplayValue('旧场次')
    await user.clear(heading)
    await user.type(heading, '新场次')

    expect(putScriptDraft).not.toHaveBeenCalled()
    expect(screen.getByText('正在保存…')).toBeInTheDocument()

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    await waitFor(() => {
      expect(putScriptDraft).toHaveBeenCalledWith(
        PROJECT_ID,
        1,
        expect.objectContaining({
          scenes: expect.arrayContaining([
            expect.objectContaining({ heading: '新场次' }),
          ]),
        }),
      )
    })

    await waitFor(() => {
      expect(screen.getByText('草稿自动保存')).toBeInTheDocument()
    })
  })

  it('shows save error, keeps dirty, and retries after failure', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

    getEpisodesState.mockResolvedValue(episodePlanCommitted())
    getScriptsState.mockResolvedValue(emptyScripts())
    getScriptEpisode.mockResolvedValue({
      episode_number: 1,
      committed: null,
      candidate: null,
      draft: {
        episode_number: 1,
        payload: {
          scenes: [{ id: 's1', heading: '旧场次', beats: [{ type: 'action', text: '旧动作' }] }],
        },
        updated_at: '2026-07-23T08:00:00Z',
      },
    })
    putScriptDraft
      .mockRejectedValueOnce(new Error('网络异常，请稍后重试'))
      .mockResolvedValue({
        episode_number: 1,
        payload: {
          scenes: [{ id: 's1', heading: '新场次', beats: [{ type: 'action', text: '旧动作' }] }],
        },
        updated_at: '2026-07-23T08:21:00Z',
      })

    renderEditor(`/projects/${PROJECT_ID}/editor?ep=1`)

    const heading = await screen.findByDisplayValue('旧场次')
    await user.clear(heading)
    await user.type(heading, '新场次')

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    await waitFor(() => {
      expect(putScriptDraft).toHaveBeenCalledTimes(1)
      expect(screen.getByText('网络异常，请稍后重试')).toBeInTheDocument()
    })
    expect(screen.getByDisplayValue('新场次')).toBeInTheDocument()

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    await waitFor(() => {
      expect(putScriptDraft).toHaveBeenCalledTimes(2)
    })
    await waitFor(() => {
      expect(screen.getByText('草稿自动保存')).toBeInTheDocument()
    })
  })

  it('flushes pending edits before switching episode', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

    getEpisodesState.mockResolvedValue(episodePlanCommitted(2))
    getScriptsState.mockResolvedValue(emptyScripts())
    getScriptEpisode.mockImplementation(async (_id: string, ep: number) => ({
      episode_number: ep,
      committed: null,
      candidate: null,
      draft: {
        episode_number: ep,
        payload: {
          scenes: [
            {
              id: 's1',
              heading: ep === 2 ? '第二集场次' : '第一集场次',
              beats: [{ type: 'action', text: '动作' }],
            },
          ],
        },
        updated_at: '2026-07-23T08:00:00Z',
      },
    }))
    putScriptDraft.mockResolvedValue({
      episode_number: 1,
      payload: {
        scenes: [{ id: 's1', heading: '已改场次', beats: [{ type: 'action', text: '动作' }] }],
      },
      updated_at: '2026-07-23T08:22:00Z',
    })

    renderEditor(`/projects/${PROJECT_ID}/editor?ep=1`)

    const heading = await screen.findByDisplayValue('第一集场次')
    await user.clear(heading)
    await user.type(heading, '已改场次')
    expect(putScriptDraft).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: /第 2 集/ }))

    await waitFor(() => {
      expect(putScriptDraft).toHaveBeenCalledWith(
        PROJECT_ID,
        1,
        expect.objectContaining({
          scenes: expect.arrayContaining([
            expect.objectContaining({ heading: '已改场次' }),
          ]),
        }),
      )
    })
    expect(await screen.findByDisplayValue('第二集场次')).toBeInTheDocument()
  })

  it('generates batch 1–2 and confirms candidate with summary', async () => {
    const user = userEvent.setup()
    getEpisodesState.mockResolvedValue(episodePlanCommitted())
    getScriptsState.mockResolvedValue(
      emptyScripts({
        candidate: makeArtifact('episode_scripts', {
          status: 'candidate',
          payload: {
            episodes: [
              {
                episode_number: 1,
                title: '候选一',
                script: '甲乙丙丁',
                word_count: 4,
                dialogue_ratio: 0.5,
                scene_count: 1,
              },
              {
                episode_number: 2,
                title: '候选二',
                script: '戊己庚辛壬癸',
                word_count: 6,
                dialogue_ratio: 0.4,
                scene_count: 1,
              },
            ],
          },
        }),
        latest_run: {
          id: '33333333-3333-4333-8333-333333333333',
          command_type: 'write_episode_batch',
          status: 'succeeded',
          project_id: PROJECT_ID,
          error_message: '',
          result_payload: {},
          created_at: '2026-07-23T08:02:00Z',
          updated_at: '2026-07-23T08:02:00Z',
        },
      }),
    )
    getScriptEpisode.mockResolvedValue({
      episode_number: 1,
      committed: null,
      candidate: {
        episode_number: 1,
        title: '候选一',
        script: '甲乙丙丁',
      },
      draft: null,
    })
    generateScriptBatch.mockResolvedValue({
      command_run: {
        id: '22222222-2222-4222-8222-222222222222',
        command_type: 'write_episode_batch',
        status: 'queued',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:01:00Z',
        updated_at: '2026-07-23T08:01:00Z',
      },
    })
    confirmScriptCandidate.mockResolvedValue({
      command_run: {
        id: '44444444-4444-4444-8444-444444444444',
        command_type: 'confirm_script_candidate',
        status: 'succeeded',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:03:00Z',
        updated_at: '2026-07-23T08:03:00Z',
      },
    })

    renderEditor()

    expect(await screen.findByText(/候选集：1、2/)).toBeInTheDocument()
    expect(screen.getByText(/候选约 10 字/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /生成本批/ }))
    await waitFor(() => {
      expect(generateScriptBatch).toHaveBeenCalledWith(PROJECT_ID, { start: 1, end: 2 })
    })

    await user.click(screen.getByRole('button', { name: '确认采用' }))
    await waitFor(() => {
      expect(confirmScriptCandidate).toHaveBeenCalledWith(PROJECT_ID, { use_drafts: false })
    })
  })

  it('honors ?episode= query for initial episode selection', async () => {
    getEpisodesState.mockResolvedValue(episodePlanCommitted(2))
    getScriptsState.mockResolvedValue(emptyScripts())
    getScriptEpisode.mockImplementation(async (_id: string, ep: number) => ({
      episode_number: ep,
      committed: null,
      candidate: null,
      draft: {
        episode_number: ep,
        payload: {
          scenes: [
            {
              id: 's1',
              heading: ep === 2 ? '第二集场次' : '第一集场次',
              beats: [{ type: 'action', text: '动作' }],
            },
          ],
        },
        updated_at: '2026-07-23T08:00:00Z',
      },
    }))

    renderEditor(`/projects/${PROJECT_ID}/editor?episode=2`)

    expect(await screen.findByDisplayValue('第二集场次')).toBeInTheDocument()
    expect(getScriptEpisode).toHaveBeenCalledWith(PROJECT_ID, 2)
  })

  it('shows jump hint when finding is present without episode', async () => {
    getEpisodesState.mockResolvedValue(episodePlanCommitted())
    getScriptsState.mockResolvedValue(emptyScripts())
    getScriptEpisode.mockResolvedValue({
      episode_number: 1,
      committed: null,
      candidate: null,
      draft: null,
    })

    renderEditor(`/projects/${PROJECT_ID}/editor?finding=defect:0`)

    expect(await screen.findByTestId('editor-jump-hint')).toHaveTextContent(
      '未定位到场次，已打开编辑器',
    )
  })

  it('does not show jump hint when episode and finding are both present', async () => {
    getEpisodesState.mockResolvedValue(episodePlanCommitted())
    getScriptsState.mockResolvedValue(emptyScripts())
    getScriptEpisode.mockResolvedValue({
      episode_number: 2,
      committed: null,
      candidate: null,
      draft: null,
    })

    renderEditor(`/projects/${PROJECT_ID}/editor?episode=2&finding=defect:0`)

    await screen.findByRole('heading', { name: '正文编辑' })
    expect(screen.queryByTestId('editor-jump-hint')).not.toBeInTheDocument()
  })

  it('honors ?ep= query for initial episode selection', async () => {
    getEpisodesState.mockResolvedValue(episodePlanCommitted(2))
    getScriptsState.mockResolvedValue(emptyScripts())
    getScriptEpisode.mockImplementation(async (_id: string, ep: number) => ({
      episode_number: ep,
      committed: null,
      candidate: null,
      draft: {
        episode_number: ep,
        payload: {
          scenes: [
            {
              id: 's1',
              heading: ep === 2 ? '第二集场次' : '第一集场次',
              beats: [{ type: 'action', text: '动作' }],
            },
          ],
        },
        updated_at: '2026-07-23T08:00:00Z',
      },
    }))

    renderEditor(`/projects/${PROJECT_ID}/editor?ep=2`)

    expect(await screen.findByDisplayValue('第二集场次')).toBeInTheDocument()
    expect(getScriptEpisode).toHaveBeenCalledWith(PROJECT_ID, 2)
  })
})
