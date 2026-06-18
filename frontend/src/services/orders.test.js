import { describe, it, expect, vi, beforeEach } from 'vitest'
import { orders } from './orders'

const mockRequest = vi.fn()

vi.mock('./http', () => ({
  request: (...args) => mockRequest(...args),
}))

describe('orders.list pagination', () => {
  beforeEach(() => {
    mockRequest.mockReset()
  })

  it('passes page and page_size and returns normalized pagination', async () => {
    mockRequest.mockResolvedValue({
      data: [{ order_no: 'SF001', status: 'paid' }],
      pagination: { total: 15, page: 2, page_size: 10, total_pages: 2 },
    })
    const result = await orders.list(undefined, { page: 2, pageSize: 10 })
    expect(mockRequest).toHaveBeenCalledWith('GET', '/api/orders/', {
      params: { page: 2, page_size: 10 },
    })
    expect(result.items).toHaveLength(1)
    expect(result.pagination.page).toBe(2)
    expect(result.pagination.total).toBe(15)
  })
})
