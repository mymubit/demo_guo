import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type {
  ArtifactVersion,
  CommandRunSummary,
  QualityState,
  ScriptsState,
} from '@/types/v3/domain'
import { QualityPage } from './QualityPage'

const getQualityState = vi.fn()
const scoreQuality = vi.fn()
const checkCompliance = vi.fn()
const acceptFindings = vi.fn()
const reviseFromFindings = vi.fn()
const getScriptsState = vi.fn()
const confirmScriptCandidate = vi.fn()
const navigateMock = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

vi.mock('@/services/v3/quality', () => ({
  getQualityState: (...args: unknown[]) => getQualityState(...args),
  scoreQuality: (...args: unknown[]) => scoreQuality(...args),
  checkCompliance: (...args: unknown[]) => checkCompliance(...args),
  acceptFindings: (...args: unknown[]) => acceptFindings(...args),
  reviseFromFindings: (...args: unknown[]) => reviseFromFindings(...args),
}))

vi.mock('@/services/v3/scripts', () => ({
  getScriptsState: (...args: unknown[]) => getScriptsState(...args),
  confirmScriptCandidate: (...args: unknown[]) => confirmScriptCandidate(...args),
}))

const PROJECT_ID = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'

function makeArtifact(
  key: string,
  overrides: Partial<ArtifactVersion> & Pick<ArtifactVersion, 'status' | 'payload'>,
): ArtifactVersion {
  return {
    id: overrides.id ?? '11111111-1111-4111-8111-111111111111',
    artifact_key: key,
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
    command_type: overrides.command_type ?? 'score_quality',
    status: overrides.status ?? 'queued',
    project_id: PROJECT_ID,
    error_message: overrides.error_message ?? '',
    result_payload: overrides.result_payload ?? {},
    created_at: overrides.created_at ?? '2026-07-23T08:01:00Z',
    updated_at: overrides.updated_at ?? '2026-07-23T08:01:00Z',
  }
}

function emptyQuality(overrides: Partial<QualityState> = {}): QualityState {
  return {
    stage: 'quality',
    quality_report: null,
    compliance_report: null,
    findings: [],
    quality_is_stale: false,
    compliance_is_stale: false,
    latest_quality_run: null,
    latest_compliance_run: null,
    ...overrides,
  }
}

function emptyScripts(overrides: Partial<ScriptsState> = {}): ScriptsState {
  return {
    committed: null,
    candidate: null,
    drafts: [],
    latest_run: null,
    ...overrides,
  }
}

function scriptsWithCommitted(): ScriptsState {
  return emptyScripts({
    committed: makeArtifact('episode_scripts', {
      status: 'committed',
      payload: { episodes: [{ episode: 1, script: '正文' }] },
    }),
  })
}

function qualityWithReport(): QualityState {
  return emptyQuality({
    quality_report: makeArtifact('quality_report', {
      status: 'committed',
      payload: {
        grade: 'A',
        overall_score: 82,
        verdict: '通过',
        dimensions: {
          format: { score: 85 },
          narrative: { score: 84 },
          conflict: { score: 83 },
          character: { score: 81 },
          emotion: { score: 80 },
          logic: { score: 82 },
          satisfaction: { score: 81 },
          hooks: { score: 84 },
          paywall: { score: 78 },
          genre_fit: { score: 82 },
        },
        defects: [
          { finding_key: 'defect:0', title: '中段节奏偏慢', severity: 'medium' },
          {
            finding_key: 'defect:ep3',
            title: '第3集对白冗长',
            severity: 'low',
            episode: 3,
          },
        ],
      },
    }),
    compliance_report: makeArtifact('compliance_report', {
      id: '33333333-3333-4333-8333-333333333333',
      status: 'committed',
      payload: {
        overall_result: '条件通过',
        blocking_issues: [
          { finding_key: 'blk-1', title: '敏感用语', description: '需改写' },
        ],
        risk_items: [{ type: 'p1', issue: '暴力描写偏多' }],
      },
    }),
  })
}

function renderQuality(projectId = PROJECT_ID) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/quality`]}>
        <Routes>
          <Route path="/projects/:id/quality" element={<QualityPage />} />
          <Route path="/projects/:id/editor" element={<div>正文编辑占位</div>} />
          <Route path="/projects/:id" element={<div>项目概览占位</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('QualityPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    navigateMock.mockReset()
  })

  it('renders Chinese UI without operation recipe ids', async () => {
    getScriptsState.mockResolvedValue(scriptsWithCommitted())
    getQualityState.mockResolvedValue(emptyQuality())

    renderQuality()

    expect(await screen.findByRole('heading', { name: '质检中心' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '质量评分' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '合规审查' })).toBeInTheDocument()
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/score-quality/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/score_quality/i)).not.toBeInTheDocument()
  })

  it('disables checks without committed scripts and links to editor', async () => {
    getScriptsState.mockResolvedValue(emptyScripts())
    getQualityState.mockResolvedValue(emptyQuality())

    renderQuality()

    expect(await screen.findByText(/请先确认剧本正文/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '质量评分' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '合规审查' })).toBeDisabled()
    expect(screen.getByRole('link', { name: '去正文编辑' })).toBeInTheDocument()
  })

  it('calls scoreQuality when score button is clicked', async () => {
    const user = userEvent.setup()
    getScriptsState.mockResolvedValue(scriptsWithCommitted())
    getQualityState.mockResolvedValue(emptyQuality())
    scoreQuality.mockResolvedValue({ command_run: makeRun() })

    renderQuality()

    expect(await screen.findByText(/尚未运行质检/)).toBeInTheDocument()
    const button = screen.getByRole('button', { name: '质量评分' })
    expect(button).toBeEnabled()
    await user.click(button)

    await waitFor(() => {
      expect(scoreQuality).toHaveBeenCalledWith(PROJECT_ID)
    })
  })

  it('shows grade, score, Chinese dimension labels and findings', async () => {
    getScriptsState.mockResolvedValue(scriptsWithCommitted())
    getQualityState.mockResolvedValue(qualityWithReport())

    renderQuality()

    expect(await screen.findByText('A')).toBeInTheDocument()
    expect(screen.getByText('82')).toBeInTheDocument()
    expect(screen.getByText('赛道匹配')).toBeInTheDocument()
    expect(screen.getByText('付费点优化')).toBeInTheDocument()
    expect(screen.getByText('中段节奏偏慢')).toBeInTheDocument()
    expect(screen.getByText('敏感用语')).toBeInTheDocument()
    expect(screen.getByText('暴力描写偏多')).toBeInTheDocument()
  })

  it('shows stale banner when reports are stale', async () => {
    getScriptsState.mockResolvedValue(scriptsWithCommitted())
    getQualityState.mockResolvedValue(
      emptyQuality({
        quality_is_stale: true,
        compliance_is_stale: false,
        quality_report: makeArtifact('quality_report', {
          status: 'committed',
          payload: { grade: 'B', overall_score: 70, dimensions: {} },
        }),
      }),
    )

    renderQuality()

    expect(await screen.findByText(/质量报告已相对正文过期/)).toBeInTheDocument()
  })

  it('batch accepts selected findings with gate-aligned keys', async () => {
    const user = userEvent.setup()
    getScriptsState.mockResolvedValue(scriptsWithCommitted())
    getQualityState.mockResolvedValue(qualityWithReport())
    acceptFindings.mockResolvedValue({
      command_run: makeRun({ command_type: 'accept_findings', status: 'succeeded' }),
    })

    renderQuality()

    expect(await screen.findByText('敏感用语')).toBeInTheDocument()
    await user.click(screen.getByRole('checkbox', { name: '选择问题：敏感用语' }))
    await user.click(screen.getByRole('button', { name: '接受已选问题' }))

    await waitFor(() => {
      expect(acceptFindings).toHaveBeenCalledWith(PROJECT_ID, {
        findings: [
          {
            source: 'compliance',
            finding_key: 'blk-1',
            title: '敏感用语',
            severity: 'blocking',
          },
        ],
      })
    })
  })

  it('revises from selected finding keys', async () => {
    const user = userEvent.setup()
    getScriptsState.mockResolvedValue(scriptsWithCommitted())
    getQualityState.mockResolvedValue(qualityWithReport())
    reviseFromFindings.mockResolvedValue({
      command_run: makeRun({ command_type: 'revise_from_findings', status: 'succeeded' }),
    })

    renderQuality()

    expect(await screen.findByText('中段节奏偏慢')).toBeInTheDocument()
    await user.click(screen.getByRole('checkbox', { name: '选择问题：中段节奏偏慢' }))
    await user.click(screen.getByRole('button', { name: '按已选问题修订' }))

    await waitFor(() => {
      expect(reviseFromFindings).toHaveBeenCalledWith(PROJECT_ID, {
        finding_keys: ['defect:0'],
      })
    })
  })

  it('navigates to editor with episode and finding when locating issue', async () => {
    const user = userEvent.setup()
    getScriptsState.mockResolvedValue(scriptsWithCommitted())
    getQualityState.mockResolvedValue(qualityWithReport())

    renderQuality()

    expect(await screen.findByText('第3集对白冗长')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '定位到正文：第3集对白冗长' }))

    expect(navigateMock).toHaveBeenCalledWith(
      `/projects/${PROJECT_ID}/editor?finding=defect%3Aep3&episode=3`,
    )
  })

  it('navigates with finding only when episode cannot be parsed', async () => {
    const user = userEvent.setup()
    getScriptsState.mockResolvedValue(scriptsWithCommitted())
    getQualityState.mockResolvedValue(qualityWithReport())

    renderQuality()

    expect(await screen.findByText('中段节奏偏慢')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '定位到正文：中段节奏偏慢' }))

    expect(navigateMock).toHaveBeenCalledWith(
      `/projects/${PROJECT_ID}/editor?finding=defect%3A0`,
    )
  })

  it('prompts to confirm script candidate after revise', async () => {
    const user = userEvent.setup()
    getScriptsState.mockResolvedValue({
      ...scriptsWithCommitted(),
      candidate: makeArtifact('episode_scripts', {
        id: '44444444-4444-4444-8444-444444444444',
        status: 'candidate',
        payload: { episodes: [{ episode: 1, script: '修订正文' }] },
      }),
    })
    getQualityState.mockResolvedValue(qualityWithReport())
    confirmScriptCandidate.mockResolvedValue({
      command_run: makeRun({ command_type: 'confirm_script_candidate', status: 'succeeded' }),
    })

    renderQuality()

    expect(await screen.findByText(/修订已生成正文候选/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '去编辑器确认' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '确认修订候选' }))

    await waitFor(() => {
      expect(confirmScriptCandidate).toHaveBeenCalledWith(PROJECT_ID, { use_drafts: false })
    })
  })
})
