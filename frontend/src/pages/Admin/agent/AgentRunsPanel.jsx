import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { admin } from '@/services/api'
import ExecutionRunPanel from '@/components/shared/ExecutionRunPanel'
import { AdminEmpty, AdminLoading, AdminMessage } from '@/components/admin/AdminUI'
import {
  AdminPenetrationLink,
  AdminWorkbench,
  adminBtnSecondary,
} from '@/components/admin/workbench/AdminWorkbenchKit'
import { adminProjectDetailPath } from '@/utils/adminProjectRoutes'
import { runStatusLabel } from '@/utils/agentExecutionLabels'

const RUNNING_POLL_MS = 5000
const STATUS_FILTERS = [
  { value: '', label: '全部状态' },
  { value: 'success', label: '成功' },
  { value: 'failed', label: '失败' },
  { value: 'running', label: '运行中' },
]

export default function AgentRunsPanel() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState('')
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [agentFilter, setAgentFilter] = useState('')
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

  const agentOptions = useMemo(() => {
    const ids = [...new Set(runs.map((r) => r.agent_id).filter(Boolean))]
    return ids.sort()
  }, [runs])

  const filteredRuns = useMemo(() => {
    return runs.filter((run) => {
      if (statusFilter && run.status !== statusFilter) return false
      if (agentFilter && run.agent_id !== agentFilter) return false
      return true
    })
  }, [runs, statusFilter, agentFilter])

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

  const toolbar = (
    <div className="flex flex-wrap items-end gap-3">
      <label className="text-xs text-navy-400">
        Agent
        <select className="sf-control mt-1 text-sm block min-w-[140px]" value={agentFilter} onChange={(e) => setAgentFilter(e.target.value)}>
          <option value="">全部</option>
          {agentOptions.map((id) => (
            <option key={id} value={id}>{id}</option>
          ))}
        </select>
      </label>
      <label className="text-xs text-navy-400">
        状态
        <select className="sf-control mt-1 text-sm block min-w-[120px]" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          {STATUS_FILTERS.map((f) => (
            <option key={f.value || 'all'} value={f.value}>{f.label}</option>
          ))}
        </select>
      </label>
      <button type="button" onClick={() => loadRuns()} className={adminBtnSecondary()}>
        <RefreshCw className="h-4 w-4" />
        刷新
      </button>
    </div>
  )

  if (loading) return <AdminLoading label="加载运行记录…" />

  return (
    <div className="space-y-3">
      <AdminMessage message={message} onClose={() => setMessage(null)} />
      <AdminWorkbench
        toolbar={toolbar}
        listItems={filteredRuns}
        selectedId={selectedId}
        onSelect={setSelectedId}
        getItemId={(run) => run.id}
        listEmpty={<AdminEmpty title="暂无匹配的运行记录" />}
        renderListItem={(run, { active, onSelect }) => (
          <button
            key={run.id}
            type="button"
            onClick={onSelect}
            className={`w-full rounded-xl px-3 py-2.5 text-left text-xs border transition ${
              active ? 'border-gold-500/35 bg-gold-400/10 text-gold-200' : 'border-transparent text-navy-200 hover:bg-white/[0.06]'
            }`}
          >
            <div className="font-medium">{run.agent_id || '—'}</div>
            <div className="mt-1 flex items-center justify-between text-navy-400">
              <span>{runStatusLabel(run.status)}</span>
              <span>{run.started_at?.slice(11, 16) || ''}</span>
            </div>
          </button>
        )}
        detailEmpty="选择一条运行记录"
      >
        {detailLoading ? (
          <AdminLoading label="加载详情…" />
        ) : detail ? (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-3 text-xs">
              <AdminPenetrationLink to={`/admin/agent?tab=definitions`} label="Agent 定义" />
              {detail.project_id ? (
                <AdminPenetrationLink
                  to={adminProjectDetailPath(detail.project_id, 'runs')}
                  label="项目详情 · runs"
                />
              ) : null}
            </div>
            <ExecutionRunPanel run={detail} />
          </div>
        ) : (
          <AdminEmpty title="选择一条运行记录查看详情" />
        )}
      </AdminWorkbench>
    </div>
  )
}
