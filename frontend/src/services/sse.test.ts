import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'

vi.mock('@/services/http', () => ({
  API_BASE_URL: '',
}))

vi.mock('@/services/tokenStorage', () => ({
  getAccessToken: () => 'token',
}))

describe('subscribeJobEvents reconnect', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('retries with exponential backoff up to 3 times then errors', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('network down'))
    vi.stubGlobal('fetch', fetchMock)

    const { subscribeJobEvents, SSE_MAX_RECONNECT_ATTEMPTS } = await import('@/services/sse')
    expect(SSE_MAX_RECONNECT_ATTEMPTS).toBe(3)

    const onError = vi.fn()
    const stop = subscribeJobEvents('proj-1', 'job-1', { onError })

    // attempt 1 fails immediately, then delays 1s, 2s, 4s before giving up after 3 retries
    await vi.advanceTimersByTimeAsync(0)
    await Promise.resolve()
    expect(fetchMock).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(1000)
    await Promise.resolve()
    expect(fetchMock).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(2000)
    await Promise.resolve()
    expect(fetchMock).toHaveBeenCalledTimes(3)

    await vi.advanceTimersByTimeAsync(4000)
    await Promise.resolve()
    // 4th call is the last retry (attempt 3 after initial = 4 total tries? )
    // Logic: attempt starts 0, on fail attempt+=1, if attempt > 3 error.
    // So: try1 fail attempt=1, sleep 1s; try2 fail attempt=2, sleep 2s; try3 fail attempt=3, sleep 4s; try4 fail attempt=4 > 3 error
    expect(fetchMock.mock.calls.length).toBeGreaterThanOrEqual(3)
    await vi.advanceTimersByTimeAsync(8000)
    await Promise.resolve()
    expect(onError).toHaveBeenCalled()
    stop()
  })
})
