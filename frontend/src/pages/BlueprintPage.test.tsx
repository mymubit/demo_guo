import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ArtifactVersion, BlueprintState, TopicState } from '@/types/v3/domain'
import { BlueprintPage } from './BlueprintPage'

const getBlueprintState = vi.fn()
const generateBlueprint = vi.fn()
const confirmBlueprint = vi.fn()
const getTopicState = vi.fn()

vi.mock('@/services/v3/blueprint', () => ({
  getBlueprintState: (...args: unknown[]) => getBlueprintState(...args),
  generateBlueprint: (...args: unknown[]) => generateBlueprint(...args),
  confirmBlueprint: (...args: unknown[]) => confirmBlueprint(...args),
}))

vi.mock('@/services/v3/topic', () => ({
  getTopicState: (...args: unknown[]) => getTopicState(...args),
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

function emptyBlueprint(overrides: Partial<BlueprintState> = {}): BlueprintState {
  return {
    committed: null,
    candidate: null,
    latest_run: null,
    ...overrides,
  }
}

function topicWithBrief(committed = true): TopicState {
  return {
    stage: committed ? 'blueprint' : 'topic',
    committed: committed
      ? makeArtifact('project_brief', {
          status: 'committed',
          payload: { title: '已确认简报' },
        })
      : null,
    candidate: null,
    draft: null,
    latest_run: null,
  }
}

function renderBlueprint(projectId = PROJECT_ID) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/blueprint`]}>
        <Routes>
          <Route path="/projects/:id/blueprint" element={<BlueprintPage />} />
          <Route path="/projects/:id/topic" element={<div>选题定调占位</div>} />
          <Route path="/projects/:id" element={<div>项目概览占位</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('BlueprintPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Chinese tabs without operation recipe ids', async () => {
    getTopicState.mockResolvedValue(topicWithBrief(true))
    getBlueprintState.mockResolvedValue(emptyBlueprint())

    renderBlueprint()

    expect(await screen.findByRole('heading', { name: '故事蓝图' })).toBeInTheDocument()
    expect(await screen.findByRole('tab', { name: '故事蓝图' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '人物' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '世界' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '情绪' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '原创性' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成蓝图' })).toBeInTheDocument()
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/compose-story-bible/i)).not.toBeInTheDocument()
  })

  it('disables generate without committed brief and shows dependency hint', async () => {
    getTopicState.mockResolvedValue(topicWithBrief(false))
    getBlueprintState.mockResolvedValue(emptyBlueprint())

    renderBlueprint()

    expect(await screen.findByText(/请先在「选题定调」确认项目简报/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成蓝图' })).toBeDisabled()
    expect(screen.getByRole('link', { name: '去选题定调' })).toBeInTheDocument()
  })

  it('calls generateBlueprint when generate is clicked with committed brief', async () => {
    const user = userEvent.setup()
    getTopicState.mockResolvedValue(topicWithBrief(true))
    getBlueprintState.mockResolvedValue(emptyBlueprint())
    generateBlueprint.mockResolvedValue({
      command_run: {
        id: '22222222-2222-4222-8222-222222222222',
        command_type: 'generate_blueprint',
        status: 'queued',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:01:00Z',
        updated_at: '2026-07-23T08:01:00Z',
      },
    })

    renderBlueprint()

    expect(await screen.findByText(/尚未生成蓝图/)).toBeInTheDocument()
    const generateButton = screen.getByRole('button', { name: '生成蓝图' })
    expect(generateButton).toBeEnabled()
    await user.click(generateButton)

    await waitFor(() => {
      expect(generateBlueprint).toHaveBeenCalledWith(PROJECT_ID)
    })
  })

  it('shows candidate content and confirms blueprint', async () => {
    const user = userEvent.setup()
    getTopicState.mockResolvedValue(topicWithBrief(true))
    getBlueprintState.mockResolvedValue(
      emptyBlueprint({
        candidate: {
          story_bible: makeArtifact('story_bible', {
            status: 'candidate',
            payload: { title: '逆袭主线', core_premise: '被抛弃后夺回一切' },
          }),
          character_system: makeArtifact('character_system', {
            id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
            status: 'candidate',
            payload: { name: '人物体系' },
          }),
        },
        latest_run: {
          id: '33333333-3333-4333-8333-333333333333',
          command_type: 'generate_blueprint',
          status: 'succeeded',
          project_id: PROJECT_ID,
          error_message: '',
          result_payload: {},
          created_at: '2026-07-23T08:02:00Z',
          updated_at: '2026-07-23T08:02:00Z',
        },
      }),
    )
    confirmBlueprint.mockResolvedValue({
      command_run: {
        id: '44444444-4444-4444-8444-444444444444',
        command_type: 'confirm_blueprint',
        status: 'succeeded',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:03:00Z',
        updated_at: '2026-07-23T08:03:00Z',
      },
    })

    renderBlueprint()

    expect((await screen.findAllByText('逆袭主线')).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByRole('button', { name: '重新生成' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '确认采用' }))

    await waitFor(() => {
      expect(confirmBlueprint).toHaveBeenCalledWith(PROJECT_ID)
    })
  })

  it('switches tab to show character candidate', async () => {
    const user = userEvent.setup()
    getTopicState.mockResolvedValue(topicWithBrief(true))
    getBlueprintState.mockResolvedValue(
      emptyBlueprint({
        candidate: {
          story_bible: makeArtifact('story_bible', {
            status: 'candidate',
            payload: { title: '主线' },
          }),
          character_system: makeArtifact('character_system', {
            id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
            status: 'candidate',
            payload: { name: '女主人物卡' },
          }),
        },
      }),
    )

    renderBlueprint()

    expect((await screen.findAllByText('主线')).length).toBeGreaterThanOrEqual(1)
    await user.click(screen.getByRole('tab', { name: '人物' }))
    expect((await screen.findAllByText('女主人物卡')).length).toBeGreaterThanOrEqual(1)
  })

  it('shows in-progress run status and disables generate', async () => {
    getTopicState.mockResolvedValue(topicWithBrief(true))
    getBlueprintState.mockResolvedValue(
      emptyBlueprint({
        latest_run: {
          id: '55555555-5555-4555-8555-555555555555',
          command_type: 'generate_blueprint',
          status: 'running',
          project_id: PROJECT_ID,
          error_message: '',
          result_payload: {},
          created_at: '2026-07-23T08:04:00Z',
          updated_at: '2026-07-23T08:04:00Z',
        },
      }),
    )

    renderBlueprint()

    expect(await screen.findByText(/最近任务：进行中/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成蓝图' })).toBeDisabled()
  })
})
