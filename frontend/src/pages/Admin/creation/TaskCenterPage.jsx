import { useEffect, useState, useCallback } from 'react'
import { RefreshCw, RotateCcw, XCircle, ChevronRight } from 'lucide-react'
import { adminTask } from '@/services/admin/task'

const STATE_OPTIONS = [
  { value: '',          label: '全部状态' },
  { value: 'pending',   label: '待执行' },
  { value: 'running',   label: '执行中' },
  { value: 'paused',    label: '已暂停' },
  { value: 'completed', label: '已完成' },
  { value: 'failed',    label: '已失败' },
  { value: 'retrying',  label: '重试中' },
  { value: 'cancelled', label: '已取消' },
]

const MODE_OPTIONS = [
  { value: '',          label: '全部模式' },
  { value: 'auto',      label: '一键生成' },
  { value: 'step',      label: '分步掌控' },
  { value: 'workspace', label: '技能工作台' },
  { value: 'retry',     label: '人工重试' },
]

const STATE_BADGE = {
  pending:   'bg-gray-100 text-gray-600',
  running:   'bg-blue-100 text-blue-700',
  paused:    'bg-yellow-100 text-yellow-700',
  completed: 'bg-green-100 text-green-700',
  failed:    'bg-red-100 text-red-700',
  retrying:  'bg-orange-100 text-orange-700',
  cancelled: 'bg-gray-100 text-gray-400',
}

function StateBadge({ state, label }) {
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${STATE_BADGE[state] || 'bg-gray-100 text-gray-500'}`}>
      {label || state}
    </span>
  )
}

function TaskRow({ task, onSelect, isSelected }) {
  return (
    <tr
      className={`border-b border-gray-100 hover:bg-blue-50 cursor-pointer transition-colors
        ${isSelected ? 'bg-blue-50' : ''}`}
      onClick={() => onSelect(task)}
    >
      <td className="px-4 py-3 text-xs font-mono text-gray-500 truncate max-w-[120px]">
        {task.id.slice(0, 8)}…
      </td>
      <td className="px-4 py-3 text-xs text-gray-700 font-mono truncate max-w-[120px]">
        {task.project_id ? task.project_id.slice(0, 8) + '…' : '—'}
      </td>
      <td className="px-4 py-3">
        <span className="text-xs text-gray-600">{task.trigger_mode_label}</span>
      </td>
      <td className="px-4 py-3">
        <StateBadge state={task.state} label={task.state_label} />
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">{task.progress_percent}%</td>
      <td className="px-4 py-3 text-xs text-gray-400">
        {task.retry_count > 0 && <span className="text-orange-500">×{task.retry_count}</span>}
      </td>
      <td className="px-4 py-3 text-xs text-gray-400">
        {task.created_at ? new Date(task.created_at).toLocaleString('zh-CN') : '—'}
      </td>
      <td className="px-4 py-3">
        <ChevronRight className="w-4 h-4 text-gray-300" />
      </td>
    </tr>
  )
}

function TaskDetail({ task, onRetry, onCancel }) {
  if (!task) return null

  const canRetry  = ['failed', 'cancelled'].includes(task.state)
  const canCancel = ['pending', 'paused'].includes(task.state)

  return (
    <div className="w-96 flex-shrink-0 border border-gray-200 rounded-lg bg-white overflow-y-auto">
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h3 className="font-semibold text-sm text-gray-800">任务详情</h3>
        <div className="flex gap-2">
          {canRetry && (
            <button onClick={() => onRetry(task)}
              className="flex items-center gap-1 text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
              <RotateCcw className="w-3 h-3" /> 重试
            </button>
          )}
          {canCancel && (
            <button onClick={() => onCancel(task)}
              className="flex items-center gap-1 text-xs px-2 py-1 border border-red-200 text-red-500 rounded hover:bg-red-50">
              <XCircle className="w-3 h-3" /> 取消
            </button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4 text-sm">
        <InfoRow label="任务 ID"    value={task.id} mono />
        <InfoRow label="项目 ID"    value={task.project_id || '—'} mono />
        <InfoRow label="触发模式"   value={task.trigger_mode_label} />
        <InfoRow label="当前状态">
          <StateBadge state={task.state} label={task.state_label} />
        </InfoRow>
        <InfoRow label="进度"       value={`${task.progress_percent}%`} />
        <InfoRow label="当前节点"   value={task.current_node_index} />
        <InfoRow label="重试次数"   value={task.retry_count} />
        <InfoRow label="Celery ID"  value={task.celery_task_id || '—'} mono />

        {task.error_code && (
          <div className="bg-red-50 border border-red-200 rounded p-3">
            <div className="text-xs font-medium text-red-700 mb-1">错误码：{task.error_code}</div>
            <div className="text-xs text-red-600 break-all">{task.error_message}</div>
          </div>
        )}

        <InfoRow label="开始时间"   value={task.started_at   ? new Date(task.started_at).toLocaleString('zh-CN')   : '—'} />
        <InfoRow label="完成时间"   value={task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '—'} />
        <InfoRow label="创建时间"   value={new Date(task.created_at).toLocaleString('zh-CN')} />

        {task.extra && Object.keys(task.extra).length > 0 && (
          <div>
            <div className="text-xs text-gray-500 mb-1">扩展参数</div>
            <pre className="text-xs bg-gray-50 rounded p-2 overflow-auto max-h-32 font-mono">
              {JSON.stringify(task.extra, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}

function InfoRow({ label, value, mono, children }) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-xs text-gray-400 w-20 flex-shrink-0">{label}</span>
      {children || (
        <span className={`text-xs text-gray-700 break-all ${mono ? 'font-mono' : ''}`}>
          {value ?? '—'}
        </span>
      )}
    </div>
  )
}

export default function TaskCenterPage() {
  const [items, setItems]           = useState([])
  const [total, setTotal]           = useState(0)
  const [page, setPage]             = useState(1)
  const [loading, setLoading]       = useState(false)
  const [selected, setSelected]     = useState(null)
  const [toast, setToast]           = useState(null)

  const [filterState,   setFilterState]   = useState('')
  const [filterMode,    setFilterMode]    = useState('')
  const [filterProject, setFilterProject] = useState('')

  const showMsg = useCallback((msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await adminTask.listCreationTasks({
        state:        filterState   || undefined,
        trigger_mode: filterMode    || undefined,
        project_id:   filterProject || undefined,
        page,
      })
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      showMsg(err.message || '加载失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [filterState, filterMode, filterProject, page, showMsg])

  useEffect(() => { load() }, [load])

  async function handleRetry(task) {
    try {
      const newTask = await adminTask.retryCreationTask(task.id)
      showMsg('重试任务已创建')
      load()
      setSelected(newTask)
    } catch (err) {
      showMsg(err.message || '重试失败', 'error')
    }
  }

  async function handleCancel(task) {
    if (!confirm('确定取消此任务？')) return
    try {
      await adminTask.cancelCreationTask(task.id)
      showMsg('任务已取消')
      load()
      setSelected(null)
    } catch (err) {
      showMsg(err.message || '取消失败', 'error')
    }
  }

  const pageSize = 20
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="flex h-full gap-4">
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded shadow-lg text-sm text-white
          ${toast.type === 'error' ? 'bg-red-500' : 'bg-green-600'}`}>
          {toast.msg}
        </div>
      )}

      {/* 主区：任务表格 */}
      <div className="flex-1 flex flex-col border border-gray-200 rounded-lg overflow-hidden bg-white">
        {/* 筛选栏 */}
        <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-3 flex-wrap">
          <select value={filterState} onChange={(e) => { setFilterState(e.target.value); setPage(1) }}
            className="text-sm border border-gray-200 rounded px-2 py-1.5 focus:outline-none">
            {STATE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <select value={filterMode} onChange={(e) => { setFilterMode(e.target.value); setPage(1) }}
            className="text-sm border border-gray-200 rounded px-2 py-1.5 focus:outline-none">
            {MODE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <input
            value={filterProject}
            onChange={(e) => { setFilterProject(e.target.value); setPage(1) }}
            className="text-sm border border-gray-200 rounded px-2 py-1.5 focus:outline-none w-48"
            placeholder="项目 ID 过滤…"
          />
          <button onClick={() => load()}
            className="ml-auto p-1.5 rounded hover:bg-gray-100 text-gray-500">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <span className="text-xs text-gray-400">共 {total} 条</span>
        </div>

        {/* 表格 */}
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                {['任务 ID', '项目 ID', '触发模式', '状态', '进度', '重试', '创建时间', ''].map((h) => (
                  <th key={h} className="px-4 py-2 text-xs font-medium text-gray-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && !loading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-400">暂无任务</td></tr>
              ) : (
                items.map((task) => (
                  <TaskRow key={task.id} task={task}
                    isSelected={selected?.id === task.id}
                    onSelect={setSelected} />
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        {totalPages > 1 && (
          <div className="px-4 py-2 border-t border-gray-100 flex items-center justify-center gap-2 text-sm">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
              className="px-2 py-1 border rounded disabled:opacity-40 hover:bg-gray-50">上一页</button>
            <span className="text-gray-500">{page} / {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
              className="px-2 py-1 border rounded disabled:opacity-40 hover:bg-gray-50">下一页</button>
          </div>
        )}
      </div>

      {/* 右侧：任务详情 */}
      <TaskDetail task={selected} onRetry={handleRetry} onCancel={handleCancel} />
    </div>
  )
}
