import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { SystemConfigState } from '@/types/v3/domain'
import { SystemPage } from './SystemPage'

const getSystemConfig = vi.fn()
const putSystemConfig = vi.fn()

vi.mock('@/services/v3/system', () => ({
  getSystemConfig: (...args: unknown[]) => getSystemConfig(...args),
  putSystemConfig: (...args: unknown[]) => putSystemConfig(...args),
}))

function makeConfig(overrides: Partial<SystemConfigState> = {}): SystemConfigState {
  return {
    revision: overrides.revision ?? 0,
    overlay: overrides.overlay ?? {},
    effective: overrides.effective ?? {
      target_platform: 'generic',
      scoring_preset: 'standard',
      pass_threshold: 75,
      platform_label_zh: '通用',
      daily_cost_alert_cny: null,
    },
  }
}

function renderSystem() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/system']}>
        <Routes>
          <Route path="/system" element={<SystemPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('SystemPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Chinese UI without operation recipe ids', async () => {
    getSystemConfig.mockResolvedValue(makeConfig())

    renderSystem()

    expect(await screen.findByRole('heading', { name: '系统配置' })).toBeInTheDocument()
    expect(await screen.findByText('当前生效配置')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '保存配置' })).toBeInTheDocument()
    expect(screen.getByText('编辑覆盖项')).toBeInTheDocument()
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/score_quality/i)).not.toBeInTheDocument()
  })

  it('shows effective summary with Chinese labels', async () => {
    getSystemConfig.mockResolvedValue(
      makeConfig({
        revision: 2,
        overlay: { target_platform: 'douyin', scoring_preset: 'rhythm_first' },
        effective: {
          target_platform: 'douyin',
          scoring_preset: 'rhythm_first',
          pass_threshold: 70,
          platform_label_zh: '抖音',
          daily_cost_alert_cny: 15,
        },
      }),
    )

    renderSystem()

    expect(await screen.findByText(/修订号：2/)).toBeInTheDocument()
    expect(screen.getByText(/目标平台：抖音/)).toBeInTheDocument()
    expect(screen.getByText(/评分预设：节奏优先/)).toBeInTheDocument()
    expect(screen.getByText(/及格阈值：70/)).toBeInTheDocument()
    expect(screen.getByText(/日费用预警阈值：15 元/)).toBeInTheDocument()
  })

  it('saves platform and scoring preset without optional threshold', async () => {
    const user = userEvent.setup()
    getSystemConfig.mockResolvedValue(makeConfig())
    putSystemConfig.mockResolvedValue(
      makeConfig({
        revision: 1,
        overlay: { target_platform: 'kuaishou', scoring_preset: 'strict' },
        effective: {
          target_platform: 'kuaishou',
          scoring_preset: 'strict',
          pass_threshold: 80,
          platform_label_zh: '快手',
          daily_cost_alert_cny: null,
        },
      }),
    )

    renderSystem()

    expect(await screen.findByLabelText('目标平台')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('目标平台'), 'kuaishou')
    await user.selectOptions(screen.getByLabelText('评分预设'), 'strict')
    await user.click(screen.getByRole('button', { name: '保存配置' }))

    await waitFor(() => {
      expect(putSystemConfig).toHaveBeenCalledWith({
        overlay: {
          target_platform: 'kuaishou',
          scoring_preset: 'strict',
        },
      })
    })
  })

  it('merges existing overlay and sends null when clearing threshold', async () => {
    const user = userEvent.setup()
    getSystemConfig.mockResolvedValue(
      makeConfig({
        revision: 1,
        overlay: {
          target_platform: 'douyin',
          scoring_preset: 'strict',
          quality_pass_threshold: 90,
        },
        effective: {
          target_platform: 'douyin',
          scoring_preset: 'strict',
          pass_threshold: 90,
          platform_label_zh: '抖音',
          daily_cost_alert_cny: null,
        },
      }),
    )
    putSystemConfig.mockResolvedValue(
      makeConfig({
        revision: 2,
        overlay: { target_platform: 'douyin', scoring_preset: 'relaxed' },
        effective: {
          target_platform: 'douyin',
          scoring_preset: 'relaxed',
          pass_threshold: 60,
          platform_label_zh: '抖音',
          daily_cost_alert_cny: null,
        },
      }),
    )

    renderSystem()

    expect(await screen.findByLabelText('及格阈值')).toHaveValue(90)
    await user.selectOptions(screen.getByLabelText('评分预设'), 'relaxed')
    fireEvent.change(screen.getByLabelText('及格阈值'), { target: { value: '' } })
    await user.click(screen.getByRole('button', { name: '保存配置' }))

    await waitFor(() => {
      expect(putSystemConfig).toHaveBeenCalledWith({
        overlay: {
          target_platform: 'douyin',
          scoring_preset: 'relaxed',
          quality_pass_threshold: null,
        },
      })
    })
  })

  it('includes optional threshold and change reason when provided', async () => {
    const user = userEvent.setup()
    getSystemConfig.mockResolvedValue(makeConfig())
    putSystemConfig.mockResolvedValue(
      makeConfig({
        revision: 1,
        overlay: {
          target_platform: 'generic',
          scoring_preset: 'standard',
          quality_pass_threshold: 88,
        },
        effective: {
          target_platform: 'generic',
          scoring_preset: 'standard',
          pass_threshold: 88,
          platform_label_zh: '通用',
          daily_cost_alert_cny: null,
        },
      }),
    )

    renderSystem()

    expect(await screen.findByLabelText('及格阈值')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('及格阈值'), { target: { value: '88' } })
    fireEvent.change(screen.getByLabelText('变更说明'), { target: { value: '提高及格线' } })
    await user.click(screen.getByRole('button', { name: '保存配置' }))

    await waitFor(() => {
      expect(putSystemConfig).toHaveBeenCalledWith({
        overlay: {
          target_platform: 'generic',
          scoring_preset: 'standard',
          quality_pass_threshold: 88,
        },
        change_reason: '提高及格线',
      })
    })
  })

  it('saves daily cost alert threshold', async () => {
    const user = userEvent.setup()
    getSystemConfig.mockResolvedValue(makeConfig())
    putSystemConfig.mockResolvedValue(
      makeConfig({
        revision: 1,
        overlay: {
          target_platform: 'generic',
          scoring_preset: 'standard',
          daily_cost_alert_cny: 30,
        },
        effective: {
          target_platform: 'generic',
          scoring_preset: 'standard',
          pass_threshold: 75,
          platform_label_zh: '通用',
          daily_cost_alert_cny: 30,
        },
      }),
    )

    renderSystem()

    expect(await screen.findByLabelText('日费用预警阈值（元）')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('日费用预警阈值（元）'), {
      target: { value: '30' },
    })
    await user.click(screen.getByRole('button', { name: '保存配置' }))

    await waitFor(() => {
      expect(putSystemConfig).toHaveBeenCalledWith({
        overlay: {
          target_platform: 'generic',
          scoring_preset: 'standard',
          daily_cost_alert_cny: 30,
        },
      })
    })
  })

  it('shows load error in Chinese', async () => {
    getSystemConfig.mockRejectedValue(new Error('网络异常'))

    renderSystem()

    expect(await screen.findByText(/网络异常/)).toBeInTheDocument()
    expect(screen.queryByText('当前生效配置')).not.toBeInTheDocument()
  })
})
