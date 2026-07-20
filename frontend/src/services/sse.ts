import { API_BASE_URL } from './http'
import { getAccessToken } from './tokenStorage'
import type { SseJobEvent } from '@/types/domain'

export type SseHandlers = {
  onEvent?: (event: SseJobEvent) => void
  onError?: (error: Error) => void
  onDone?: () => void
}

const MAX_RECONNECT_ATTEMPTS = 3
const BASE_RECONNECT_DELAY_MS = 1000

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException('Aborted', 'AbortError'))
      return
    }
    const timer = setTimeout(resolve, ms)
    const onAbort = () => {
      clearTimeout(timer)
      reject(new DOMException('Aborted', 'AbortError'))
    }
    signal.addEventListener('abort', onAbort, { once: true })
  })
}

/**
 * Generation Job SSE client with exponential backoff reconnect (max 3).
 */
export function subscribeJobEvents(
  projectId: string | null,
  jobId: string,
  handlers: SseHandlers,
): () => void {
  const url = projectId
    ? `${API_BASE_URL}/api/v1/drama/projects/${projectId}/generation/${jobId}/stream/`
    : `${API_BASE_URL}/api/v1/drama/jobs/${jobId}/stream/`
  const token = getAccessToken()
  const controller = new AbortController()
  let closed = false
  let finished = false

  function finish(): void {
    if (finished || closed) return
    finished = true
    handlers.onDone?.()
  }

  async function connectOnce(): Promise<'done' | 'retry'> {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(`SSE 连接失败：HTTP ${response.status}`)
    }
    if (!response.body) {
      throw new Error('SSE 响应无内容流')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let sawTerminal = false

    while (!closed) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const chunks = buffer.split(/\n\n/)
      buffer = chunks.pop() ?? ''
      for (const chunk of chunks) {
        const dataLine = chunk
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.replace(/^data:\s?/, ''))
          .join('\n')
        if (!dataLine) continue
        try {
          const parsed = JSON.parse(dataLine) as SseJobEvent
          handlers.onEvent?.(parsed)
          if (
            parsed.type === 'done' ||
            parsed.type === 'error' ||
            parsed.type === 'timeout' ||
            parsed.done ||
            parsed.status === 'completed' ||
            parsed.status === 'failed' ||
            parsed.status === 'disabled'
          ) {
            sawTerminal = true
            finish()
          }
        } catch {
          handlers.onEvent?.({
            type: 'log',
            job_id: jobId,
            message: dataLine,
          })
        }
      }
    }

    if (sawTerminal || finished) return 'done'
    // Stream ended without terminal event — allow reconnect
    return 'retry'
  }

  async function run(): Promise<void> {
    let attempt = 0
    while (!closed && !finished) {
      try {
        const result = await connectOnce()
        if (result === 'done' || finished) return
        attempt += 1
        if (attempt > MAX_RECONNECT_ATTEMPTS) {
          handlers.onError?.(new Error('SSE 重连次数已达上限'))
          return
        }
        const delay = BASE_RECONNECT_DELAY_MS * 2 ** (attempt - 1)
        await sleep(delay, controller.signal)
      } catch (err) {
        if (closed || (err instanceof DOMException && err.name === 'AbortError')) return
        attempt += 1
        if (attempt > MAX_RECONNECT_ATTEMPTS) {
          handlers.onError?.(err instanceof Error ? err : new Error(String(err)))
          return
        }
        const delay = BASE_RECONNECT_DELAY_MS * 2 ** (attempt - 1)
        try {
          await sleep(delay, controller.signal)
        } catch {
          return
        }
      }
    }
  }

  void run()

  return () => {
    closed = true
    controller.abort()
  }
}

export const SSE_MAX_RECONNECT_ATTEMPTS = MAX_RECONNECT_ATTEMPTS
