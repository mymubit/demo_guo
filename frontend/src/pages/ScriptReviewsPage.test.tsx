import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ScriptReviewDetail, ScriptReviewSummary } from '@/types/v3/domain'
import { ScriptReviewDetailPage } from './ScriptReviewDetailPage'
import { ScriptReviewNewPage } from './ScriptReviewNewPage'
import { ScriptReviewsPage } from './ScriptReviewsPage'

const listScriptReviews = vi.fn()
const createScriptReview = vi.fn()
const getScriptReview = vi.fn()
const scoreScriptReview = vi.fn()
const navigateMock = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

vi.mock('@/services/v3/reviews', () => ({
  listScriptReviews: (...args: unknown[]) => listScriptReviews(...args),
  createScriptReview: (...args: unknown[]) => createScriptReview(...args),
  createScriptReviewUpload: vi.fn(),
  getScriptReview: (...args: unknown[]) => getScriptReview(...args),
  scoreScriptReview: (...args: unknown[]) => scoreScriptReview(...args),
  checkScriptReviewCompliance: vi.fn(),
  compareScriptReviewRuns: vi.fn(),
}))

function renderRoutes(path: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/reviews" element={<ScriptReviewsPage />} />
          <Route path="/reviews/new" element={<ScriptReviewNewPage />} />
          <Route path="/reviews/:id" element={<ScriptReviewDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ScriptReviews pages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows empty state on list', async () => {
    listScriptReviews.mockResolvedValue({ items: [] as ScriptReviewSummary[] })
    renderRoutes('/reviews')
    await waitFor(() => {
      expect(screen.getByTestId('reviews-empty')).toBeInTheDocument()
    })
  })

  it('creates review from paste tab', async () => {
    const user = userEvent.setup()
    createScriptReview.mockResolvedValue({
      id: 'rev-1',
      title: '测试稿',
      source_type: 'paste',
      source_filename: '',
      project_id: null,
      project_title: null,
      script_text: '正文',
      runs: [],
      latest_quality_score: null,
      latest_quality_grade: null,
      latest_compliance_result: null,
      created_at: null,
      updated_at: null,
    } satisfies ScriptReviewDetail)

    renderRoutes('/reviews/new')
    await user.type(screen.getByTestId('script-text-input'), '第一场对白')
    await user.click(screen.getByTestId('create-review-submit'))

    await waitFor(() => {
      expect(createScriptReview).toHaveBeenCalled()
      expect(navigateMock).toHaveBeenCalledWith('/reviews/rev-1', { replace: true })
    })
  })

  it('triggers score on detail page', async () => {
    const user = userEvent.setup()
    getScriptReview.mockResolvedValue({
      id: 'rev-2',
      title: '详情稿',
      source_type: 'paste',
      source_filename: '',
      project_id: null,
      project_title: null,
      script_text: '正文内容',
      runs: [],
      latest_quality_score: null,
      latest_quality_grade: null,
      latest_compliance_result: null,
      created_at: null,
      updated_at: null,
    } satisfies ScriptReviewDetail)
    scoreScriptReview.mockResolvedValue({
      run: {
        id: 'run-1',
        kind: 'quality',
        status: 'queued',
        command_run_id: null,
        report_payload: {},
        error_message: '',
        created_at: null,
        finished_at: null,
      },
    })

    renderRoutes('/reviews/rev-2')
    await waitFor(() => {
      expect(screen.getByTestId('score-review')).toBeInTheDocument()
    })
    await user.click(screen.getByTestId('score-review'))
    await waitFor(() => {
      expect(scoreScriptReview).toHaveBeenCalledWith('rev-2')
    })
  })
})
