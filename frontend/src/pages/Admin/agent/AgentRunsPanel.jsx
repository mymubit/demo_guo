import { useCallback, useEffect, useRef, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { admin } from '@/services/api'
import ExecutionRunPanel from '@/components/shared/ExecutionRunPanel'
import { AdminEmpty, AdminLoading, AdminMessage } from '@/components/admin/AdminUI'
import { runStatusLabel } from '@/utils/agentExecutionLabels'

const RUNNING_POLL_MS = 5000

export default function AgentRunsPanel() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState('')
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const selectedIdRef = useRef(selectedId)

  useEffect(() => {
    selectedIdRef.current = selectedId
  }, [selectedId])

  const loadRuns = useCallback(async ({ silent = false } = {}) => {
    if (!silent) setLoading(true)
    try {
      const rows = await admin.listIndependentAgentRuns({ limit: 40 })
      setRuns(rows)
      setMessage(null)
      if (rows[0]?.id && !selectedIdRef.current) {
        setSelectedId(rows[0].id)
      }
    } catch (err) {
      setRuns([])
      setMessage({ type: 'error', text: err.message || '加载运行记录失败' })
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRuns()
  }, [loadRuns])

  const hasRunning = runs.some((run) => run.status === 'running')

  useEffect(() => {
    if (!hasRunning) return undefined
    const timer = setInterval(() => {
      loadRuns({ silent: true })
    }, RUNNING_POLL_MS)
    return () => clearInterval(timer)
  }, [hasRunning, loadRuns])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      return undefined
    }
    let cancelled = false
    ;(async () => {
      setDetailLoading(true)
      try {
        const row = await admin.agentExecutionRun(selectedId)
        if (!cancelled) {
          setDetail(row)
          setMessage(null)
        }
      } catch (err) {
        if (!cancelled) {
          setDetail(null)
          setMessage({ type: 'error', text: err.message || '加载运行详情失败' })
        }
      } finally {
        if (!cancelled) setDetailLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selectedId])

  if (loading) return <AdminLoading label="加载运行记录…" />

  return (
    <div className="space-y-3">
      <AdminMessage message={message} onClose={() => setMessage(null)} />
      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => loadRuns()}
          className="inline-flex items-center gap-1 rounded-lg border border-navy-600 px-3 py-1.5 text-xs text-navy-200 hover:bg-navy-800/80"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          刷新
        </button>
      </div>
      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <div className="space-y-2 rounded-xl border border-navy-700/60 bg-navy-900/40 p-3">
          <p className="text-xs font-medium text-navy-300">最近执行</p>
          {runs.length === 0 ? (
            <AdminEmpty title={message ? '加载失败' : '暂无运行记录'} />
          ) : (
            <ul className="max-h-[520px] space-y-1 overflow-y-auto">
              {runs.map((run) => (
                <li key={run.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(run.id)}
                    className={`w-full rounded-lg px-2 py-2 text-left text-xs transition ${
                      selectedId === run.id
                        ? 'bg-gold-500/15 text-gold-200'
                        : 'text-navy-200 hover:bg-navy-800/80'
                    }`}
                  >
                    <div className="font-medium">{run.agent_id || '—'}</div>
                    <div className="text-navy-400">{runStatusLabel(run.status)}</div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="rounded-xl border border-navy-700/60 bg-navy-900/40 p-4">
          {detailLoading ? (
            <AdminLoading label="加载详情…" />
          ) : detail ? (
            <ExecutionRunPanel run={detail} />
          ) : (
            <AdminEmpty
              title={message?.type === 'error' ? '详情加载失败' : '选择一条运行记录查看详情'}
            />
          )}
        </div>
      </div>
    </div>
  )
}
