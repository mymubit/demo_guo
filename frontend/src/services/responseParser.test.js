import { describe, it, expect } from 'vitest'
import { unwrapApiEnvelope } from './responseParser'

describe('unwrapApiEnvelope', () => {
  it('returns data on success code 0', () => {
    const out = unwrapApiEnvelope({ code: 0, message: 'success', data: { id: 1 } })
    expect(out.ok).toBe(true)
    expect(out.value).toEqual({ id: 1 })
  })

  it('returns data and pagination when present', () => {
    const out = unwrapApiEnvelope({
      code: 0,
      message: 'success',
      data: [{ id: 1 }],
      pagination: { total: 1, page: 1, page_size: 10, total_pages: 1 },
    })
    expect(out.ok).toBe(true)
    expect(out.value.data).toEqual([{ id: 1 }])
    expect(out.value.pagination.total).toBe(1)
  })

  it('returns error envelope for business failure', () => {
    const out = unwrapApiEnvelope({ code: 4001, message: '参数错误', data: null })
    expect(out.ok).toBe(false)
    expect(out.code).toBe(4001)
    expect(out.message).toBe('参数错误')
  })

  it('passes through raw SimpleJWT refresh shape', () => {
    const raw = { access: 'token-abc' }
    const out = unwrapApiEnvelope(raw)
    expect(out.ok).toBe(true)
    expect(out.value).toEqual(raw)
  })
})
