import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { GenerationJobPanel } from '@/components/workbench/GenerationJobPanel'
import type { GenerationJob } from '@/types/domain'

const subscribeJobEvents = vi.fn()
const getGenerationStatus = vi.fn()

vi.mock('@/services/sse', () => ({
  subscribeJobEvents: (...args: unknown[]) => subscribeJobEvents(...args),
}))

vi.mock('@/services/drama', () => ({
  dramaApi: {
    getGenerationStatus: (...args: unknown[]) => getGenerationStatus(...args),
    getJob: vi.fn(),
  },
}))

describe('GenerationJobPanel', () => {
  beforeEach(() => {
    subscribeJobEvents.mockReset()
    getGenerationStatus.mockReset()
  })

  it('refreshes status on SSE done and calls onCompleted only for success', async () => {
    const job: GenerationJob = {
      job_id: 'job-1',
      project_id: 'proj-1',
      status: 'running',
      role: 'drama.topic-director',
      command_id: 'cmd-1',
    }
    getGenerationStatus.mockResolvedValue({ ...job, status: 'completed' })
    subscribeJobEvents.mockImplementation((_projectId, _jobId, handlers) => {
      handlers.onDone()
      return () => undefined
    })

    const onCompleted = vi.fn()
    render(<GenerationJobPanel projectId="proj-1" job={job} onCompleted={onCompleted} />)

    await waitFor(() => {
      expect(getGenerationStatus).toHaveBeenCalledWith('proj-1', 'job-1')
    })
    expect(onCompleted).toHaveBeenCalled()
    expect(screen.getByText('已完成')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('does not treat failed as success and shows Chinese trouble card', async () => {
    const job: GenerationJob = {
      job_id: 'job-2',
      project_id: 'proj-1',
      status: 'running',
      role: 'drama.topic-director',
      command_id: 'cmd-2',
    }
    getGenerationStatus.mockResolvedValue({
      ...job,
      status: 'failed',
      error: 'LLM 配置不完整',
    })
    subscribeJobEvents.mockImplementation((_projectId, _jobId, handlers) => {
      handlers.onDone()
      return () => undefined
    })

    const onCompleted = vi.fn()
    render(
      <MemoryRouter>
        <GenerationJobPanel projectId="proj-1" job={job} onCompleted={onCompleted} />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(getGenerationStatus).toHaveBeenCalled()
    })
    expect(onCompleted).not.toHaveBeenCalled()
    expect(screen.getByText('失败')).toBeInTheDocument()
    expect(await screen.findByText('模型配置不完整')).toBeInTheDocument()
    expect(screen.getByText('前往模型管理 →')).toBeInTheDocument()
  })

  it('does not treat disabled as success and guides to model hub', async () => {
    const job: GenerationJob = {
      job_id: 'job-3',
      project_id: 'proj-1',
      status: 'running',
      role: 'drama.topic-director',
      command_id: 'cmd-3',
    }
    getGenerationStatus.mockResolvedValue({
      ...job,
      status: 'disabled',
      error: 'LLM 不可用 (disabled)',
    })
    subscribeJobEvents.mockImplementation((_projectId, _jobId, handlers) => {
      handlers.onDone()
      return () => undefined
    })

    const onCompleted = vi.fn()
    render(
      <MemoryRouter>
        <GenerationJobPanel projectId="proj-1" job={job} onCompleted={onCompleted} />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(getGenerationStatus).toHaveBeenCalled()
    })
    expect(onCompleted).not.toHaveBeenCalled()
    expect(screen.getByText('已禁用')).toBeInTheDocument()
    expect(await screen.findByText('模型未启用')).toBeInTheDocument()
  })

  it('subscribes once per job_id (effect does not re-subscribe on progress)', () => {
    const job: GenerationJob = {
      job_id: 'job-4',
      project_id: 'proj-1',
      status: 'running',
      progress: 10,
      role: 'drama.topic-director',
      command_id: 'cmd-4',
    }
    subscribeJobEvents.mockReturnValue(() => undefined)

    const { rerender } = render(<GenerationJobPanel projectId="proj-1" job={job} />)
    expect(subscribeJobEvents).toHaveBeenCalledTimes(1)

    rerender(
      <GenerationJobPanel
        projectId="proj-1"
        job={{ ...job, status: 'running', progress: 80 }}
      />,
    )
    expect(subscribeJobEvents).toHaveBeenCalledTimes(1)
  })
})
