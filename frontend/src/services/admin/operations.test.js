/**
 * services/admin/operations.test.js —— 【运营 F2】operations 服务单测
 */
import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest'

import { adminOperations } from './operations'

vi.mock('./http', () => ({
  adminRequest: vi.fn(() => Promise.resolve({ data: {} })),
}))

import { adminRequest } from './http'

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('adminOperations.dashboard', () => {
  it('GET /api/admin/operations/dashboard/ with days', () => {
    adminOperations.dashboard({ days: 30 })
    expect(adminRequest).toHaveBeenCalledWith('GET', '/api/admin/operations/dashboard/', { params: { days: 30 } })
  })
})

describe('adminOperations.contentQuality', () => {
  it('GET /api/admin/operations/content-quality/', () => {
    adminOperations.contentQuality({ days: 7 })
    expect(adminRequest).toHaveBeenCalledWith('GET', '/api/admin/operations/content-quality/', { params: { days: 7 } })
  })
})

describe('adminOperations.feedback', () => {
  it('list 调用 unwrapAdminList', async () => {
    adminRequest.mockResolvedValueOnce({ data: { items: [], pagination: { total: 0 } } })
    const res = await adminOperations.feedback.list({ page: 1 })
    expect(adminRequest).toHaveBeenCalledWith('GET', '/api/admin/operations/feedback/', { params: { page: 1 } })
    expect(res.items).toEqual([])
  })

  it('summary GET /api/admin/operations/feedback/summary/', () => {
    adminOperations.feedback.summary({ days: 7 })
    expect(adminRequest).toHaveBeenCalledWith('GET', '/api/admin/operations/feedback/summary/', { params: { days: 7 } })
  })

  it('patch 携带 id + body', () => {
    adminOperations.feedback.patch('fb-1', { status: 'resolved' })
    expect(adminRequest).toHaveBeenCalledWith('PATCH', '/api/admin/operations/feedback/fb-1/', { data: { status: 'resolved' } })
  })

  it('remove 调用 DELETE', () => {
    adminOperations.feedback.remove('fb-1')
    expect(adminRequest).toHaveBeenCalledWith('DELETE', '/api/admin/operations/feedback/fb-1/')
  })
})

describe('adminOperations.configHit', () => {
  it('GET with limit', () => {
    adminOperations.configHit({ limit: 30 })
    expect(adminRequest).toHaveBeenCalledWith('GET', '/api/admin/operations/config-hit/', { params: { limit: 30 } })
  })
})

describe('adminOperations.samples', () => {
  it('list 透传 params', () => {
    adminOperations.samples.list({ days: 7, limit: 10 })
    expect(adminRequest).toHaveBeenCalledWith('GET', '/api/admin/operations/samples/', { params: { days: 7, limit: 10 } })
  })

  it('mark 传 project_ids', () => {
    adminOperations.samples.mark(['p1', 'p2'])
    expect(adminRequest).toHaveBeenCalledWith('POST', '/api/admin/operations/samples/mark/', {
      data: { project_ids: ['p1', 'p2'] },
    })
  })
})

describe('adminOperations.behavior', () => {
  it('list GET /behavior/', () => {
    adminOperations.behavior.list({ days: 7 })
    expect(adminRequest).toHaveBeenCalledWith('GET', '/api/admin/operations/behavior/', { params: { days: 7 } })
  })
})
