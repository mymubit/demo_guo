import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ArtifactVersion, TopicState } from '@/types/v3/domain'
import { TopicPage } from './TopicPage'

const getTopicState = vi.fn()
const generateTopicBrief = vi.fn()
const confirmTopicBrief = vi.fn()
const saveTopicDraft = vi.fn()

vi.mock('@/services/v3/topic', () => ({
  getTopicState: (...args: unknown[]) => getTopicState(...args),
  generateTopicBrief: (...args: unknown[]) => generateTopicBrief(...args),
  confirmTopicBrief: (...args: unknown[]) => confirmTopicBrief(...args),
  saveTopicDraft: (...args: unknown[]) => saveTopicDraft(...args),
}))

const PROJECT_ID = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'

function makeArtifact(
  overrides: Partial<ArtifactVersion> & Pick<ArtifactVersion, 'status' | 'payload'>,
): ArtifactVersion {
  return {
    id: overrides.id ?? '11111111-1111-4111-8111-111111111111',
    artifact_key: 'project_brief',
    version: overrides.version ?? 1,
    schema_version: 1,
    status: overrides.status,
    payload: overrides.payload,
    created_at: overrides.created_at ?? '2026-07-23T08:00:00Z',
  }
}

function emptyTopic(overrides: Partial<TopicState> = {}): TopicState {
  return {
    stage: 'topic',
    committed: null,
    candidate: null,
    draft: null,
    latest_run: null,
    ...overrides,
  }
}

function renderTopic(projectId = PROJECT_ID) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/topic`]}>
        <Routes>
          <Route path="/projects/:id/topic" element={<TopicPage />} />
          <Route path="/projects/:id" element={<div>项目概览占位</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('TopicPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Chinese UI without operation recipe ids', async () => {
    getTopicState.mockResolvedValue(emptyTopic())

    renderTopic()

    expect(await screen.findByRole('heading', { name: '选题定调' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成简报' })).toBeInTheDocument()
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/create-project-brief/i)).not.toBeInTheDocument()
  })

  it('shows committed brief title and selling point', async () => {
    getTopicState.mockResolvedValue(
      emptyTopic({
        stage: 'blueprint',
        committed: makeArtifact({
          status: 'committed',
          payload: {
            title: '重生之逆袭人生',
            core_idea: '被抛弃后夺回一切',
            target_audience: '都市女性',
          },
        }),
      }),
    )

    renderTopic()

    expect(await screen.findByText('已确认简报')).toBeInTheDocument()
    expect(screen.getAllByText('重生之逆袭人生').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('被抛弃后夺回一切').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/故事蓝图/)).toBeInTheDocument()
  })

  it('calls generateTopicBrief when generate button is clicked', async () => {
    const user = userEvent.setup()
    getTopicState.mockResolvedValue(emptyTopic())
    generateTopicBrief.mockResolvedValue({
      command_run: {
        id: '22222222-2222-4222-8222-222222222222',
        command_type: 'generate_topic_brief',
        status: 'queued',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:01:00Z',
        updated_at: '2026-07-23T08:01:00Z',
      },
    })

    renderTopic()

    await screen.findByRole('button', { name: '生成简报' })
    await user.click(screen.getByRole('button', { name: '生成简报' }))

    await waitFor(() => {
      expect(generateTopicBrief).toHaveBeenCalledWith(PROJECT_ID)
    })
  })

  it('shows confirm button for candidate and calls confirmTopicBrief', async () => {
    const user = userEvent.setup()
    getTopicState.mockResolvedValue(
      emptyTopic({
        candidate: makeArtifact({
          status: 'candidate',
          payload: { title: '候选标题', core_idea: '候选卖点' },
        }),
        latest_run: {
          id: '33333333-3333-4333-8333-333333333333',
          command_type: 'generate_topic_brief',
          status: 'succeeded',
          project_id: PROJECT_ID,
          error_message: '',
          result_payload: {},
          created_at: '2026-07-23T08:02:00Z',
          updated_at: '2026-07-23T08:02:00Z',
        },
      }),
    )
    confirmTopicBrief.mockResolvedValue({
      command_run: {
        id: '44444444-4444-4444-8444-444444444444',
        command_type: 'confirm_topic_brief',
        status: 'succeeded',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:03:00Z',
        updated_at: '2026-07-23T08:03:00Z',
      },
    })

    renderTopic()

    expect(await screen.findByText('候选简报')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '重新生成' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '确认采用' }))

    await waitFor(() => {
      expect(confirmTopicBrief).toHaveBeenCalledWith(PROJECT_ID, undefined)
    })
  })

  it('shows in-progress run status in Chinese', async () => {
    getTopicState.mockResolvedValue(
      emptyTopic({
        latest_run: {
          id: '55555555-5555-4555-8555-555555555555',
          command_type: 'generate_topic_brief',
          status: 'running',
          project_id: PROJECT_ID,
          error_message: '',
          result_payload: {},
          created_at: '2026-07-23T08:04:00Z',
          updated_at: '2026-07-23T08:04:00Z',
        },
      }),
    )

    renderTopic()

    expect(await screen.findByText(/最近任务：进行中/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成简报' })).toBeDisabled()
  })

  it('saves draft JSON via saveTopicDraft', async () => {
    const user = userEvent.setup()
    const draftPayload = { title: '草稿标题', core_idea: '草稿卖点' }
    getTopicState.mockResolvedValue(emptyTopic())
    saveTopicDraft.mockResolvedValue(
      makeArtifact({
        id: '66666666-6666-4666-8666-666666666666',
        status: 'draft',
        payload: draftPayload,
      }),
    )

    renderTopic()

    const textarea = await screen.findByLabelText('选题草稿')
    await user.clear(textarea)
    await user.paste(JSON.stringify(draftPayload))
    await user.click(screen.getByRole('button', { name: '保存草稿' }))

    await waitFor(() => {
      expect(saveTopicDraft).toHaveBeenCalledWith(PROJECT_ID, draftPayload)
    })
  })
})
