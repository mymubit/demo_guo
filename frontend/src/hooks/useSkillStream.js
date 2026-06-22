import { useCallback, useRef, useState } from 'react'
import { API_BASE_URL, getAccessToken } from '@/services/http'

const DEFAULT_PROTOCOL = '1.2'

function parseSseBlock(block) {
  let eventType = 'message'
  let dataText = ''
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) eventType = line.slice(6).trim()
    if (line.startsWith('data:')) dataText += line.slice(5).trim()
  }
  if (!dataText) return null
  try {
    return { eventType, data: JSON.parse(dataText) }
  } catch {
    return { eventType, data: { raw: dataText } }
  }
}

/**
 * Agent 流式 SSE Hook（fetch + ReadableStream，支持 POST body）
 */
export function useSkillStream() {
  const [items, setItems] = useState([])
  const [tokens, setTokens] = useState('')
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)
  const [meta, setMeta] = useState(null)
  const abortRef = useRef(null)

  const reset = useCallback(() => {
    setItems([])
    setTokens('')
    setStatus('idle')
    setError(null)
    setMeta(null)
  }, [])

  const stop = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setStatus((prev) => (prev === 'streaming' ? 'stopped' : prev))
  }, [])

  const startStream = useCallback(async (projectId, agentId, params = {}) => {
    reset()
    setStatus('streaming')
    const controller = new AbortController()
    abortRef.current = controller

    const token = getAccessToken()
    const url = `${API_BASE_URL}/api/creation/projects/${projectId}/agents/${agentId}/stream/`
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ params }),
      signal: controller.signal,
    })

    if (!resp.ok || !resp.body) {
      setStatus('error')
      setError(`流式请求失败 (${resp.status})`)
      return
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''
        for (const part of parts) {
          const parsed = parseSseBlock(part)
          if (!parsed) continue
          const { eventType, data } = parsed
          if (eventType === 'start') {
            setMeta(data)
            if (data.protocol_version && data.protocol_version !== DEFAULT_PROTOCOL) {
              console.warn('[useSkillStream] protocol mismatch', data.protocol_version)
            }
          } else if (eventType === 'token') {
            setTokens((prev) => prev + (data.delta || ''))
          } else if (eventType === 'item') {
            setItems((prev) => {
              const next = [...prev]
              next[data.item_index ?? next.length] = {
                effectiveIndex: data.effective_index,
                data: data.data,
              }
              return next.filter(Boolean)
            })
          } else if (eventType === 'done') {
            setStatus('done')
            setMeta((prev) => ({ ...(prev || {}), done: data }))
          } else if (eventType === 'error') {
            setStatus('error')
            setError(data.message || '流式生成失败')
          }
        }
      }
      setStatus((prev) => (prev === 'streaming' ? 'done' : prev))
    } catch (err) {
      if (err?.name === 'AbortError') {
        setStatus('stopped')
      } else {
        setStatus('error')
        setError(err?.message || '流式连接中断')
      }
    } finally {
      abortRef.current = null
    }
  }, [reset])

  return {
    items,
    tokens,
    status,
    error,
    meta,
    startStream,
    stop,
    reset,
  }
}

export default useSkillStream
