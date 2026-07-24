import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type {
  ArtifactVersion,
  CommandRunSummary,
  DeliveryState,
} from '@/types/v3/domain'
import { DeliveryPage } from './DeliveryPage'

const getDeliveryState = vi.fn()
const prepareDelivery = vi.fn()
const exportDeliveryDocx = vi.fn()

vi.mock('@/services/v3/delivery', () => ({
  getDeliveryState: (...args: unknown[]) => getDeliveryState(...args),
  prepareDelivery: (...args: unknown[]) => prepareDelivery(...args),
  exportDeliveryDocx: (...args: unknown[]) => exportDeliveryDocx(...args),
}))

const PROJECT_ID = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'

function makeArtifact(
  overrides: Partial<ArtifactVersion> & Pick<ArtifactVersion, 'status' | 'payload'>,
): ArtifactVersion {
  return {
    id: overrides.id ?? '11111111-1111-4111-8111-111111111111',
    artifact_key: 'production_package',
    version: overrides.version ?? 1,
    schema_version: 1,
    status: overrides.status,
    payload: overrides.payload,
    created_at: overrides.created_at ?? '2026-07-23T08:00:00Z',
  }
}

function makeRun(overrides: Partial<CommandRunSummary> = {}): CommandRunSummary {
  return {
    id: overrides.id ?? '22222222-2222-4222-8222-222222222222',
    command_type: overrides.command_type ?? 'prepare_delivery',
    status: overrides.status ?? 'queued',
    project_id: PROJECT_ID,
    error_message: overrides.error_message ?? '',
    result_payload: overrides.result_payload ?? {},
    created_at: overrides.created_at ?? '2026-07-23T08:01:00Z',
    updated_at: overrides.updated_at ?? '2026-07-23T08:01:00Z',
  }
}

function emptyDelivery(overrides: Partial<DeliveryState> = {}): DeliveryState {
  return {
    stage: 'quality',
    gate: { passed: false, blockers: ['请先确认正文后再交付'] },
    package: null,
    latest_run: null,
    ...overrides,
  }
}

function packagePayload() {
  return {
    drama_title: '测试短剧',
    source_artifact: 'latest_script',
    storyboard: [{ title: '镜1' }],
    visual_assets: [{ title: '视觉1' }, { title: '视觉2' }],
    marketing_assets: [],
    production_plan: {
      complexity_score: 40,
      complexity_band: 'standard',
      cost_drivers: ['室内对白戏为主'],
      high_cost_scenes: [],
      lower_cost_alternatives: ['用特写替代群戏'],
    },
    release_checklist: {
      target_platform: 'generic',
      policy_version: null,
      verified_at: null,
      blocking_items: [],
      missing_materials: [],
      can_release: true,
    },
  }
}

function renderDelivery(projectId = PROJECT_ID) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/delivery`]}>
        <Routes>
          <Route path="/projects/:id/delivery" element={<DeliveryPage />} />
          <Route path="/projects/:id/quality" element={<div>质检占位</div>} />
          <Route path="/projects/:id" element={<div>项目概览占位</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DeliveryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Chinese UI without operation recipe ids', async () => {
    getDeliveryState.mockResolvedValue(emptyDelivery())

    renderDelivery()

    expect(await screen.findByRole('heading', { name: '交付中心' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成交付包' })).toBeInTheDocument()
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/prepare-delivery/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/prepare_delivery/i)).not.toBeInTheDocument()
  })

  it('shows Chinese blockers and disables prepare when gate fails', async () => {
    getDeliveryState.mockResolvedValue(
      emptyDelivery({
        gate: {
          passed: false,
          blockers: ['需要有效的质量报告，请重新评分', '合规审查未通过'],
        },
      }),
    )

    renderDelivery()

    expect(await screen.findByText('交付门禁：未通过')).toBeInTheDocument()
    expect(screen.getByText('需要有效的质量报告，请重新评分')).toBeInTheDocument()
    expect(screen.getByText('合规审查未通过')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '生成交付包' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '下载 Word' })).toBeDisabled()
    expect(screen.getByRole('link', { name: '去质检中心' })).toBeInTheDocument()
  })

  it('enables prepare when gate passed and calls prepareDelivery', async () => {
    const user = userEvent.setup()
    getDeliveryState.mockResolvedValue(
      emptyDelivery({
        gate: { passed: true, blockers: [] },
      }),
    )
    prepareDelivery.mockResolvedValue({ command_run: makeRun() })

    renderDelivery()

    expect(await screen.findByText('交付门禁：已通过')).toBeInTheDocument()
    expect(screen.getByText('PDF 请使用浏览器打印为 PDF')).toBeInTheDocument()
    const button = screen.getByRole('button', { name: '生成交付包' })
    expect(button).toBeEnabled()
    expect(screen.getByRole('button', { name: '下载 Word' })).toBeEnabled()
    await user.click(button)

    await waitFor(() => {
      expect(prepareDelivery).toHaveBeenCalledWith(PROJECT_ID)
    })
  })

  it('shows package summary and download actions', async () => {
    getDeliveryState.mockResolvedValue(
      emptyDelivery({
        stage: 'delivery',
        gate: { passed: true, blockers: [] },
        package: makeArtifact({
          status: 'committed',
          payload: packagePayload(),
        }),
      }),
    )

    renderDelivery()

    expect((await screen.findAllByText('测试短剧')).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('标准').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/分镜 1 · 视觉 2 ·\s*营销 0/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '下载 JSON' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '下载 Markdown' })).toBeInTheDocument()
  })

  it('downloads JSON and Markdown via browser Blob only', async () => {
    const user = userEvent.setup()
    const createObjectURL = vi.fn((_blob: Blob) => 'blob:mock-url')
    const revokeObjectURL = vi.fn()
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined)
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL,
      revokeObjectURL,
    })

    getDeliveryState.mockResolvedValue(
      emptyDelivery({
        stage: 'delivery',
        gate: { passed: true, blockers: [] },
        package: makeArtifact({
          status: 'committed',
          payload: packagePayload(),
        }),
      }),
    )

    renderDelivery()
    expect(await screen.findByRole('button', { name: '下载 JSON' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '下载 JSON' }))
    await user.click(screen.getByRole('button', { name: '下载 Markdown' }))

    expect(createObjectURL).toHaveBeenCalledTimes(2)
    expect(revokeObjectURL).toHaveBeenCalledTimes(2)
    expect(clickSpy).toHaveBeenCalledTimes(2)
    const blobs = createObjectURL.mock.calls.map((call) => call[0])
    expect(blobs[0]).toBeInstanceOf(Blob)
    expect(blobs[1]).toBeInstanceOf(Blob)
    expect(blobs[0]?.type).toContain('application/json')
    expect(blobs[1]?.type).toContain('text/markdown')

    clickSpy.mockRestore()
    vi.unstubAllGlobals()
  })

  it('downloads Word via exportDeliveryDocx blob', async () => {
    const user = userEvent.setup()
    const docxBlob = new Blob(['PK'], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
    exportDeliveryDocx.mockResolvedValue(docxBlob)
    const createObjectURL = vi.fn((_blob: Blob) => 'blob:docx-url')
    const revokeObjectURL = vi.fn()
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined)
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL,
      revokeObjectURL,
    })

    getDeliveryState.mockResolvedValue(
      emptyDelivery({
        gate: { passed: true, blockers: [] },
      }),
    )

    renderDelivery()
    const wordButton = await screen.findByRole('button', { name: '下载 Word' })
    expect(wordButton).toBeEnabled()
    await user.click(wordButton)

    await waitFor(() => {
      expect(exportDeliveryDocx).toHaveBeenCalledWith(PROJECT_ID)
    })
    expect(createObjectURL).toHaveBeenCalledOnce()
    expect(createObjectURL.mock.calls[0]?.[0]).toBe(docxBlob)
    expect(revokeObjectURL).toHaveBeenCalledOnce()
    expect(clickSpy).toHaveBeenCalledOnce()

    clickSpy.mockRestore()
    vi.unstubAllGlobals()
  })
})
