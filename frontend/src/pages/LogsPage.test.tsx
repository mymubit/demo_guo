import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type {
  CommandRunSummary,
  FailoverAttempt,
  LogCall,
  LogRun,
  ProjectSummary,
} from '@/types/v3/domain'
import { LogsPage } from './LogsPage'

const listLogRuns = vi.fn()
const getLogRun = vi.fn()
const getLogCall = vi.fn()
const listProjects = vi.fn()

vi.mock('@/services/v3/logs', () => ({
  listLogRuns: (...args: unknown[]) => listLogRuns(...args),
  getLogRun: (...args: unknown[]) => getLogRun(...args),
  getLogCall: (...args: unknown[]) => getLogCall(...args),
}))

vi.mock('@/services/v3/projects', () => ({
  listProjects: (...args: unknown[]) => listProjects(...args),
}))

function makeProject(overrides: Partial<ProjectSummary> = {}): ProjectSummary {
  return {
    id: overrides.id ?? 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    title: overrides.title ?? '测试项目',
    entry_type: overrides.entry_type ?? 'original',
    stage: overrides.stage ?? 'topic',
    archived_at: overrides.archived_at ?? null,
    updated_at: overrides.updated_at ?? '2026-07-23T00:00:00Z',
  }
}

function makeRun(overrides: Partial<CommandRunSummary> = {}): CommandRunSummary {
  return {
    id: overrides.id ?? '11111111-1111-1111-1111-111111111111',
    command_type: overrides.command_type ?? 'generate_topic_brief',
    status: overrides.status ?? 'succeeded',
    project_id: overrides.project_id ?? 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    error_message: overrides.error_message ?? '',
    result_payload: overrides.result_payload ?? {},
    created_at: overrides.created_at ?? '2026-07-23T10:00:00Z',
    updated_at: overrides.updated_at ?? '2026-07-23T10:01:00Z',
  }
}

function makeCall(overrides: Partial<LogCall> = {}): LogCall {
  return {
    id: overrides.id ?? '22222222-2222-2222-2222-222222222222',
    role: overrides.role ?? 'drama-topic-director',
    purpose: overrides.purpose ?? 'artifact_generation',
    status: overrides.status ?? 'success',
    model_name: overrides.model_name ?? 'gpt-test',
    latency_ms: overrides.latency_ms ?? 120,
    system_prompt: overrides.system_prompt ?? '系统提示预览',
    user_prompt: overrides.user_prompt ?? '用户提示预览',
    response_text: overrides.response_text ?? '{"ok":true}',
    error_message: overrides.error_message ?? '',
    v3_command_run_id: overrides.v3_command_run_id ?? '11111111-1111-1111-1111-111111111111',
    v3_project_id: overrides.v3_project_id ?? 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    created_at: overrides.created_at ?? '2026-07-23T10:00:30Z',
  }
}

function makeFailoverAttempt(overrides: Partial<FailoverAttempt> = {}): FailoverAttempt {
  return {
    id: overrides.id ?? '44444444-4444-4444-4444-444444444444',
    attempt_index: overrides.attempt_index ?? 0,
    provider_id: overrides.provider_id ?? '55555555-5555-5555-5555-555555555555',
    provider_name: overrides.provider_name ?? '主供应商',
    status: overrides.status ?? 'failed_switchable',
    error_code: overrides.error_code ?? 'http_503',
    error_message: overrides.error_message ?? '服务不可用',
    llm_call_log_id: overrides.llm_call_log_id ?? null,
    created_at: overrides.created_at ?? '2026-07-23T10:00:10Z',
  }
}

function makeDetail(overrides: Partial<LogRun> = {}): LogRun {
  const base = makeRun(overrides)
  return {
    ...base,
    calls: overrides.calls ?? [makeCall({ v3_command_run_id: base.id })],
    failover_attempts: overrides.failover_attempts ?? [],
  }
}

function renderLogs(initialPath = '/logs') {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/projects/:id" element={<div>项目概览</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

async function selectDefaultProject(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByTestId('logs-project-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'))
}

describe('LogsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listProjects.mockResolvedValue([makeProject()])
    listLogRuns.mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 })
  })

  it('requires project selection before listing runs', async () => {
    renderLogs()

    expect(await screen.findByRole('heading', { name: '执行日志' })).toBeInTheDocument()
    expect(await screen.findByText('请先选择项目')).toBeInTheDocument()
    expect(listLogRuns).not.toHaveBeenCalled()
    expect(screen.queryByLabelText('项目')).not.toBeInTheDocument()
  })

  it('lists runs only after selecting a project', async () => {
    const user = userEvent.setup()
    listLogRuns.mockResolvedValue({ items: [makeRun()], total: 1, limit: 20, offset: 0 })

    renderLogs()
    await selectDefaultProject(user)

    expect(await screen.findByRole('button', { name: /生成选题简报/ })).toBeInTheDocument()
    await waitFor(() => {
      expect(listLogRuns).toHaveBeenCalledWith(
        expect.objectContaining({
          project_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        }),
      )
    })
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/create-project-brief/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('option', { name: '试连模型' })).not.toBeInTheDocument()
  })

  it('applies status and command filters within selected project', async () => {
    const user = userEvent.setup()
    const project = makeProject({
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      title: '筛选项目',
    })
    listProjects.mockResolvedValue([project])
    listLogRuns.mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 })

    renderLogs()
    await user.click(await screen.findByTestId(`logs-project-${project.id}`))
    await user.selectOptions(screen.getByLabelText('状态'), 'failed')
    await user.selectOptions(screen.getByLabelText('命令类型'), 'score_quality')

    await waitFor(() => {
      expect(listLogRuns).toHaveBeenLastCalledWith(
        expect.objectContaining({
          project_id: project.id,
          status: 'failed',
          command_type: 'score_quality',
        }),
      )
    })
  })

  it('honors ?project= deep link', async () => {
    const project = makeProject()
    listProjects.mockResolvedValue([project])
    listLogRuns.mockResolvedValue({ items: [makeRun()], total: 1, limit: 20, offset: 0 })

    renderLogs(`/logs?project=${project.id}`)

    expect(await screen.findByRole('button', { name: /生成选题简报/ })).toBeInTheDocument()
    await waitFor(() => {
      expect(listLogRuns).toHaveBeenCalledWith(
        expect.objectContaining({ project_id: project.id }),
      )
    })
  })

  it('opens run detail with calls and expands prompt/response in mono', async () => {
    const user = userEvent.setup()
    const run = makeRun()
    const detail = makeDetail({
      ...run,
      calls: [
        makeCall({
          system_prompt: '完整系统提示',
          user_prompt: '完整用户提示',
          response_text: '完整模型响应',
        }),
      ],
    })
    listLogRuns.mockResolvedValue({ items: [run], total: 1, limit: 20, offset: 0 })
    getLogRun.mockResolvedValue(detail)
    getLogCall.mockResolvedValue({
      ...detail.calls[0],
      system_prompt: '完整系统提示',
      user_prompt: '完整用户提示',
      response_text: '完整模型响应',
    })

    renderLogs()
    await selectDefaultProject(user)
    await user.click(await screen.findByRole('button', { name: /生成选题简报/ }))

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('调用明细')).toBeInTheDocument()
    expect(getLogRun).toHaveBeenCalledWith(run.id)

    await user.click(within(dialog).getByRole('button', { name: /展开提示与响应/ }))

    await waitFor(() => {
      expect(getLogCall).toHaveBeenCalledWith(detail.calls[0].id)
    })

    expect(await within(dialog).findByText('完整系统提示')).toBeInTheDocument()
    expect(within(dialog).getByText('完整用户提示')).toBeInTheDocument()
    expect(within(dialog).getByText('完整模型响应')).toBeInTheDocument()

    expect(within(dialog).getByTestId('log-md-block')).toBeInTheDocument()
    const monoBlocks = within(dialog).getAllByTestId('log-mono-block')
    expect(monoBlocks.length).toBeGreaterThanOrEqual(2)
    for (const block of monoBlocks) {
      expect(block.className).toMatch(/font-mono/)
    }
  })

  it('downloads current detail as JSON blob', async () => {
    const user = userEvent.setup()
    const run = makeRun()
    const detail = makeDetail({ ...run })
    listLogRuns.mockResolvedValue({ items: [run], total: 1, limit: 20, offset: 0 })
    getLogRun.mockResolvedValue(detail)

    const createObjectURL = vi.fn((_blob: Blob) => 'blob:mock-url')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL,
      revokeObjectURL,
    })

    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    renderLogs()
    await selectDefaultProject(user)
    await user.click(await screen.findByRole('button', { name: /生成选题简报/ }))
    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: '下载 JSON' }))

    expect(createObjectURL).toHaveBeenCalled()
    const blob = createObjectURL.mock.calls[0][0] as Blob
    expect(blob).toBeInstanceOf(Blob)
    expect(blob.type).toContain('json')
    expect(clickSpy).toHaveBeenCalled()

    clickSpy.mockRestore()
    vi.unstubAllGlobals()
  })

  it('shows list load error after project selected', async () => {
    const user = userEvent.setup()
    listLogRuns.mockRejectedValue(new Error('网络异常'))

    renderLogs()
    await selectDefaultProject(user)

    expect(await screen.findByText(/网络异常|加载失败|请求失败/)).toBeInTheDocument()
  })

  it('redacts operation.* and recipe-like ids in expanded prompt body', async () => {
    const user = userEvent.setup()
    const run = makeRun()
    const leakyPrompt = JSON.stringify(
      {
        command_type: 'score_quality',
        recipe_id: 'score-script',
        hint: 'see operation.score-script for details',
      },
      null,
      2,
    )
    const detail = makeDetail({
      ...run,
      calls: [
        makeCall({
          system_prompt: 'safe system',
          user_prompt: leakyPrompt,
          response_text: 'ok',
        }),
      ],
    })
    listLogRuns.mockResolvedValue({ items: [run], total: 1, limit: 20, offset: 0 })
    getLogRun.mockResolvedValue(detail)
    getLogCall.mockResolvedValue({
      ...detail.calls[0],
      system_prompt: 'safe system',
      user_prompt: leakyPrompt,
      response_text: 'ok',
    })

    renderLogs()
    await selectDefaultProject(user)
    await user.click(await screen.findByRole('button', { name: /生成选题简报/ }))
    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: /展开提示与响应/ }))

    await waitFor(() => {
      expect(getLogCall).toHaveBeenCalledWith(detail.calls[0].id)
    })

    expect(within(dialog).queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(within(dialog).queryByText(/score-script/i)).not.toBeInTheDocument()
    expect(within(dialog).getAllByText(/〔已隐藏〕/).length).toBeGreaterThan(0)
  })

  it('shows failover attempts section with provider name and Chinese status', async () => {
    const user = userEvent.setup()
    const run = makeRun()
    const detail = makeDetail({
      ...run,
      failover_attempts: [
        makeFailoverAttempt({
          provider_name: '主供应商',
          status: 'failed_switchable',
          attempt_index: 0,
        }),
        makeFailoverAttempt({
          id: '66666666-6666-6666-6666-666666666666',
          provider_id: '77777777-7777-7777-7777-777777777777',
          provider_name: '备选供应商',
          status: 'succeeded',
          attempt_index: 1,
          error_code: '',
          error_message: '',
        }),
      ],
    })
    listLogRuns.mockResolvedValue({ items: [run], total: 1, limit: 20, offset: 0 })
    getLogRun.mockResolvedValue(detail)

    renderLogs()
    await selectDefaultProject(user)
    await user.click(await screen.findByRole('button', { name: /生成选题简报/ }))

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('切换尝试')).toBeInTheDocument()
    expect(within(dialog).getByText('主供应商')).toBeInTheDocument()
    expect(within(dialog).getByText('可切换失败')).toBeInTheDocument()
    expect(within(dialog).getByText('备选供应商')).toBeInTheDocument()
    expect(within(dialog).getAllByText('成功').length).toBeGreaterThanOrEqual(1)
  })
})
