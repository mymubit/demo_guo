import { beforeEach, describe, expect, it, vi } from 'vitest'
import { http } from '@/services/http'
import { listBillingPlans } from './billing'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
  },
}))

const mockGet = vi.mocked(http.get)

describe('v3 billing service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('listBillingPlans GETs /api/v3/billing/plans/ and returns items', async () => {
    const items = [
      {
        id: 'basic',
        name: '基础版',
        price_label: '¥99/月',
        features: ['每月 3 项目'],
      },
      {
        id: 'pro',
        name: '专业版',
        price_label: '¥299/月',
        features: ['每月 10 项目'],
      },
      {
        id: 'team',
        name: '团队版',
        price_label: '¥999/月',
        features: ['不限项目/集数'],
      },
    ]
    mockGet.mockResolvedValue({ items })

    const result = await listBillingPlans()

    expect(mockGet).toHaveBeenCalledOnce()
    expect(mockGet).toHaveBeenCalledWith('/api/v3/billing/plans/')
    expect(result).toEqual(items)
  })
})
