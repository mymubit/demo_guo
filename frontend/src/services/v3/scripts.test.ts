import { beforeEach, describe, expect, it, vi } from 'vitest'
import { http } from '@/services/http'
import {
  confirmScriptCandidate,
  generateScriptBatch,
  getScriptEpisode,
  getScriptsState,
  putScriptDraft,
} from './scripts'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}))

const mockGet = vi.mocked(http.get)
const mockPost = vi.mocked(http.post)
const mockPut = vi.mocked(http.put)

const PROJECT_ID = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'

describe('v3 scripts service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getScriptsState GETs /api/v3/projects/{id}/scripts/', async () => {
    mockGet.mockResolvedValue({ committed: null, candidate: null, drafts: [], latest_run: null })
    await getScriptsState(PROJECT_ID)
    expect(mockGet).toHaveBeenCalledWith(`/api/v3/projects/${PROJECT_ID}/scripts/`)
  })

  it('getScriptEpisode GETs episode detail path', async () => {
    mockGet.mockResolvedValue({
      episode_number: 2,
      committed: null,
      candidate: null,
      draft: null,
    })
    await getScriptEpisode(PROJECT_ID, 2)
    expect(mockGet).toHaveBeenCalledWith(`/api/v3/projects/${PROJECT_ID}/scripts/2/`)
  })

  it('putScriptDraft PUTs payload body', async () => {
    const payload = { scenes: [{ id: 's1', heading: '场', beats: [] }] }
    mockPut.mockResolvedValue({ episode_number: 1, payload, updated_at: '2026-07-23T08:00:00Z' })
    await putScriptDraft(PROJECT_ID, 1, payload)
    expect(mockPut).toHaveBeenCalledWith(`/api/v3/projects/${PROJECT_ID}/scripts/1/draft/`, {
      payload,
    })
  })

  it('generateScriptBatch POSTs start/end', async () => {
    mockPost.mockResolvedValue({
      command_run: {
        id: '1',
        command_type: 'write_episode_batch',
        status: 'queued',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:00:00Z',
        updated_at: '2026-07-23T08:00:00Z',
      },
    })
    await generateScriptBatch(PROJECT_ID, { start: 1, end: 2 })
    expect(mockPost).toHaveBeenCalledWith(`/api/v3/projects/${PROJECT_ID}/scripts/generate/`, {
      start: 1,
      end: 2,
    })
  })

  it('confirmScriptCandidate POSTs use_drafts flag', async () => {
    mockPost.mockResolvedValue({
      command_run: {
        id: '2',
        command_type: 'confirm_script_candidate',
        status: 'succeeded',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:00:00Z',
        updated_at: '2026-07-23T08:00:00Z',
      },
    })
    await confirmScriptCandidate(PROJECT_ID, { use_drafts: false })
    expect(mockPost).toHaveBeenCalledWith(`/api/v3/projects/${PROJECT_ID}/scripts/confirm/`, {
      use_drafts: false,
    })
  })
})
