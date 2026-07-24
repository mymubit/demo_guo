import { beforeEach, describe, expect, it, vi } from 'vitest'
import { http } from '@/services/http'
import { getDeliveryState, prepareDelivery, exportDeliveryDocx } from './delivery'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

const mockGet = vi.mocked(http.get)
const mockPost = vi.mocked(http.post)

const PROJECT_ID = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'

describe('v3 delivery service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getDeliveryState GETs /api/v3/projects/{id}/delivery/', async () => {
    mockGet.mockResolvedValue({
      stage: 'quality',
      gate: { passed: false, blockers: ['请先确认正文后再交付'] },
      package: null,
      latest_run: null,
    })

    await getDeliveryState(PROJECT_ID)

    expect(mockGet).toHaveBeenCalledOnce()
    expect(mockGet).toHaveBeenCalledWith(`/api/v3/projects/${PROJECT_ID}/delivery/`)
  })

  it('prepareDelivery POSTs /api/v3/projects/{id}/delivery/prepare/', async () => {
    mockPost.mockResolvedValue({
      command_run: {
        id: '22222222-2222-4222-8222-222222222222',
        command_type: 'prepare_delivery',
        status: 'queued',
        project_id: PROJECT_ID,
        error_message: '',
        result_payload: {},
        created_at: '2026-07-23T08:00:00Z',
        updated_at: '2026-07-23T08:00:00Z',
      },
    })

    await prepareDelivery(PROJECT_ID)

    expect(mockPost).toHaveBeenCalledOnce()
    expect(mockPost).toHaveBeenCalledWith(
      `/api/v3/projects/${PROJECT_ID}/delivery/prepare/`,
      {},
    )
  })

  it('exportDeliveryDocx POSTs blob from /delivery/export/docx/', async () => {
    const blob = new Blob(['PK'], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
    mockPost.mockResolvedValue(blob)

    const result = await exportDeliveryDocx(PROJECT_ID)

    expect(mockPost).toHaveBeenCalledOnce()
    expect(mockPost).toHaveBeenCalledWith(
      `/api/v3/projects/${PROJECT_ID}/delivery/export/docx/`,
      {},
      { rawResponse: true, responseType: 'blob' },
    )
    expect(result).toBe(blob)
  })
})
