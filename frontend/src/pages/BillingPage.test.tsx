import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { BillingPlan } from '@/types/v3/domain'
import { BillingPage } from './BillingPage'

const listBillingPlans = vi.fn()

vi.mock('@/services/v3/billing', () => ({
  listBillingPlans: (...args: unknown[]) => listBillingPlans(...args),
}))

const SAMPLE_PLANS: BillingPlan[] = [
  {
    id: 'basic',
    name: '基础版',
    price_label: '¥99/月',
    features: ['每月 3 项目', '每项目最多 30 集', '基础评分/合规'],
  },
  {
    id: 'pro',
    name: '专业版',
    price_label: '¥299/月',
    features: ['每月 10 项目', '十维评分', '分镜+宣发'],
  },
  {
    id: 'team',
    name: '团队版',
    price_label: '¥999/月',
    features: ['不限项目/集数', '5 席位协作', 'API'],
  },
]

function renderBilling() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/billing']}>
        <Routes>
          <Route path="/billing" element={<BillingPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('BillingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders three plan cards with Chinese names and prices', async () => {
    listBillingPlans.mockResolvedValue(SAMPLE_PLANS)

    renderBilling()

    expect(await screen.findByRole('heading', { name: '套餐' })).toBeInTheDocument()
    expect(await screen.findByText('基础版')).toBeInTheDocument()
    expect(screen.getByText('专业版')).toBeInTheDocument()
    expect(screen.getByText('团队版')).toBeInTheDocument()
    expect(screen.getByText('¥99/月')).toBeInTheDocument()
    expect(screen.getByText('¥299/月')).toBeInTheDocument()
    expect(screen.getByText('¥999/月')).toBeInTheDocument()
    expect(screen.getByText('每月 3 项目')).toBeInTheDocument()
    expect(screen.getByText('十维评分')).toBeInTheDocument()
    expect(screen.getByText('5 席位协作')).toBeInTheDocument()
  })

  it('marks pro plan as featured', async () => {
    listBillingPlans.mockResolvedValue(SAMPLE_PLANS)

    renderBilling()

    const proCard = await screen.findByTestId('billing-plan-pro')
    expect(proCard).toHaveAttribute('data-featured', 'true')
    expect(within(proCard).getByText('最受欢迎')).toBeInTheDocument()

    expect(screen.getByTestId('billing-plan-basic')).toHaveAttribute('data-featured', 'false')
    expect(screen.getByTestId('billing-plan-team')).toHaveAttribute('data-featured', 'false')
  })

  it('shows shell footnote and disables purchase with 即将开放', async () => {
    listBillingPlans.mockResolvedValue(SAMPLE_PLANS)

    renderBilling()

    expect(await screen.findByText('当前为展示壳，无支付与配额')).toBeInTheDocument()

    const buttons = screen.getAllByRole('button', { name: '即将开放' })
    expect(buttons).toHaveLength(3)
    for (const button of buttons) {
      expect(button).toBeDisabled()
    }
  })

  it('does not surface operation ids', async () => {
    listBillingPlans.mockResolvedValue(SAMPLE_PLANS)

    renderBilling()

    await screen.findByText('专业版')
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/billing\./i)).not.toBeInTheDocument()
  })

  it('shows load error in Chinese', async () => {
    listBillingPlans.mockRejectedValue(new Error('网络异常'))

    renderBilling()

    expect(await screen.findByText(/网络异常/)).toBeInTheDocument()
    expect(screen.queryByText('基础版')).not.toBeInTheDocument()
  })
})
