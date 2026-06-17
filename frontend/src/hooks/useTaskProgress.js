/**
 * useTaskProgress — SSE 实时创作进度 Hook
 *
 * 替代 ProjectWorkspace 中的自适应 HTTP 轮询逻辑：
 *   - 订阅 /api/creation/projects/{projectId}/progress/stream/ SSE 接口
 *   - 自动重连（网络断开 / 5 分钟超时后）
 *   - 连接失败时自动 fallback 到单次 HTTP 轮询模式
 *
 * 使用方式：
 *   const { state, isConnected, error } = useTaskProgress(projectId, {
 *     enabled: isBusy,             // 仅在项目进行中时启用
 *     onProgress: (state) => ...,  // 每次收到进度更新的回调
 *     onDone: (state) => ...,      // 完成时回调
 *     onError: (state) => ...,     // 失败时回调
 *   })
 *
 * 注意：
 *   - SSE 连接需要鉴权 Cookie（同域请求自动携带，跨域需配置 withCredentials）
 *   - 服务端超时（5分钟）后会发 timeout 事件，此 Hook 自动重连
 *   - 若浏览器不支持 EventSource，自动 fallback 到 disabled 模式
 */
import { useCallback, useEffect, useRef, useState } from 'react'

const SSE_BASE = '/api/creation/projects'
const MAX_RETRY_DELAY_MS = 30_000
const INITIAL_RETRY_DELAY_MS = 2_000

/**
 * @typedef {Object} TaskProgressState
 * @property {string} status           - running / completed / failed / pending
 * @property {string} fusion_status    - planning / writing / reviewing / scoring / ready / blocked
 * @property {number} progress_percent - 0-100
 * @property {number} current_node_index
 * @property {number} total_nodes
 * @property {string} error_message
 */

/**
 * @param {string} projectId
 * @param {object} options
 * @param {boolean} [options.enabled=true]
 * @param {function} [options.onProgress]
 * @param {function} [options.onDone]
 * @param {function} [options.onError]
 * @returns {{ state: TaskProgressState|null, isConnected: boolean, error: string|null }}
 */
export function useTaskProgress(projectId, options = {}) {
  const { enabled = true, onProgress, onDone, onError } = options

  const [state, setState]           = useState(null)
  const [isConnected, setConnected] = useState(false)
  const [error, setError]           = useState(null)

  const esRef         = useRef(null)
  const retryCountRef = useRef(0)
  const retryTimerRef = useRef(null)
  const mountedRef    = useRef(true)

  const onProgressRef = useRef(onProgress)
  const onDoneRef     = useRef(onDone)
  const onErrorRef    = useRef(onError)
  onProgressRef.current = onProgress
  onDoneRef.current     = onDone
  onErrorRef.current    = onError

  const connect = useCallback(() => {
    if (!projectId || !enabled || !mountedRef.current) return
    if (!window.EventSource) {
      setError('浏览器不支持 SSE，将使用 HTTP 轮询')
      return
    }

    // 关闭旧连接
    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }

    const url = `${SSE_BASE}/${projectId}/progress/stream/`
    const es  = new EventSource(url, { withCredentials: true })
    esRef.current = es

    es.onopen = () => {
      if (!mountedRef.current) return
      setConnected(true)
      setError(null)
      retryCountRef.current = 0
    }

    es.addEventListener('progress', (evt) => {
      if (!mountedRef.current) return
      try {
        const data = JSON.parse(evt.data)
        setState(data)
        onProgressRef.current?.(data)
      } catch {
        // JSON 解析失败忽略
      }
    })

    es.addEventListener('done', (evt) => {
      if (!mountedRef.current) return
      try {
        const data = JSON.parse(evt.data)
        setState(data)
        onDoneRef.current?.(data)
      } catch {}
      es.close()
      setConnected(false)
    })

    es.addEventListener('error', (evt) => {
      if (!mountedRef.current) return
      try {
        const data = JSON.parse(evt.data || '{}')
        setState(data)
        onErrorRef.current?.(data)
      } catch {}
      es.close()
      setConnected(false)
    })

    es.addEventListener('timeout', () => {
      if (!mountedRef.current) return
      es.close()
      setConnected(false)
      // 超时后延迟重连
      scheduleRetry()
    })

    es.onerror = () => {
      if (!mountedRef.current) return
      setConnected(false)
      es.close()
      scheduleRetry()
    }
  }, [projectId, enabled])

  const scheduleRetry = useCallback(() => {
    if (!mountedRef.current) return
    const delay = Math.min(
      INITIAL_RETRY_DELAY_MS * 2 ** retryCountRef.current,
      MAX_RETRY_DELAY_MS,
    )
    retryCountRef.current += 1
    retryTimerRef.current = window.setTimeout(() => {
      if (mountedRef.current) connect()
    }, delay)
  }, [connect])

  useEffect(() => {
    mountedRef.current = true
    if (enabled && projectId) {
      connect()
    }
    return () => {
      mountedRef.current = false
      if (esRef.current) {
        esRef.current.close()
        esRef.current = null
      }
      if (retryTimerRef.current) {
        window.clearTimeout(retryTimerRef.current)
      }
    }
  }, [projectId, enabled, connect])

  return { state, isConnected, error }
}
