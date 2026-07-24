import { beforeEach, describe, expect, it, vi } from 'vitest'
import { http } from '@/services/http'
import { archiveProject, listProjects } from './projects'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

const mockGet = vi.mocked(http.get)
const mockPost = vi.mocked(http.post)

describe('v3 projects service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('listProjects calls GET /api/v3/projects/ without include_archived by default', async () => {
    mockGet.mockResolvedValue({ items: [] })

    await listProjects()

    expect(mockGet).toHaveBeenCalledOnce()
    expect(mockGet).toHaveBeenCalledWith('/api/v3/projects/', undefined)
  })

  it('listProjects passes include_archived=1 when includeArchived is true', async () => {
    mockGet.mockResolvedValue({ items: [] })

    await listProjects(true)

    expect(mockGet).toHaveBeenCalledWith('/api/v3/projects/', {
      params: { include_archived: 1 },
    })
  })

  it('archiveProject POSTs to /api/v3/projects/{id}/archive/', async () => {
    const project = {
      id: '11111111-1111-4111-8111-111111111111',
      title: '归档测试',
      entry_type: 'original' as const,
      stage: 'topic' as const,
      archived_at: '2026-07-23T01:00:00Z',
      updated_at: '2026-07-23T01:00:00Z',
    }
    mockPost.mockResolvedValue(project)

    const result = await archiveProject(project.id)

    expect(mockPost).toHaveBeenCalledOnce()
    expect(mockPost).toHaveBeenCalledWith(
      '/api/v3/projects/11111111-1111-4111-8111-111111111111/archive/',
    )
    expect(result).toEqual(project)
  })
})
