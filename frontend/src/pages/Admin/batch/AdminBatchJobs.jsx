import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  RefreshCw,
  Play,
  Pause,
  RotateCcw,
  ChevronDown,
  ChevronRight,
  Upload,
  FileText,
} from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { adminBatch } from '@/services/admin/batch'
import { adminWorkflow } from '@/services/admin/workflow'
import {
  AdminPageHeader,
  AdminPanel,
  AdminTable,
  AdminPagination,
  AdminLoading,
  AdminMessage,
  AdminBadge,
  AdminToolbar,
  AdminSearchInput,
  AdminConfirmDialog,
  formatDateTime,
} from '@/components/admin/AdminUI'
import { cardEnter, modalOverlay, modalPanel } from '@/constants/motion'
import { cn } from '@/utils/cn'

const STATUS_OPTIONS = [
  { key: '', label: '全部状态' },
  { key: 'pending', label: '排队中' },
  { key: 'running', label: '进行中' },
  { key: 'completed', label: '已完成' },
  { key: 'failed', label: '失败' },
  { key: 'paused', label: '已暂停' },
]

const STATUS_TONE = {
  pending: 'default',
  running: 'warning',
  completed: 'success',
  failed: 'danger',
  paused: 'default',
}

const STATUS_LABEL = {
  pending: '排队中',
  running: '进行中',
  completed: '已完成',
  failed: '失败',
  paused: '已暂停',
}

const ITEM_STATUS_TONE = {
  pending: 'default',
  running: 'warning',
  completed: 'success',
  failed: 'danger',
}

function JobStatusBadge({ status }) {
  return (
    <AdminBadge tone={STATUS_TONE[status] || 'default'}>
      {STATUS_LABEL[status] || status}
    </AdminBadge>
  )
}

function ItemStatusBadge({ status }) {
  return (
    <AdminBadge tone={ITEM_STATUS_TONE[status] || 'default'}>
      {STATUS_LABEL[status] || status}
    </AdminBadge>
  )
}

/** 进度环 */
function ProgressRing({ completed, total, size = 80 }) {
  const percent = total > 0 ? (completed / total) * 100 : 0
  const r = (size - 12) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (percent / 100) * circ

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          className="text-white/10"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="text-gold-400 transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-white">{completed}</span>
        <span className="text-xs text-navy-400">/ {total}</span>
      </div>
    </div>
  )
}

/** 批量任务列表页 */
function AdminBatchJobList({ onSelect }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState(null)
  const [actionLoading, setActionLoading] = useState(null)

  const keyword = searchParams.get('q') || ''
  const status = searchParams.get('status') || ''
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10))

  const patchParams = useCallback(
    (patch, resetPage = true) => {
      const next = new URLSearchParams(searchParams)
      Object.entries(patch).forEach(([key, value]) => {
        if (value === '' || value == null) {
          next.delete(key)
        } else {
          next.set(key, String(value))
        }
      })
      if (resetPage) next.delete('page')
      setSearchParams(next, { replace: true })
    },
    [searchParams, setSearchParams]
  )

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await adminBatch.listJobs({
        page,
        page_size: 20,
        keyword: keyword.trim() || undefined,
        status: status || undefined,
      })
      setItems(res.items || [])
      setPagination({
        page: res.pagination?.page || 1,
        total_pages: res.pagination?.total_pages || 1,
        total: res.pagination?.total || 0,
        page_size: res.pagination?.page_size || 20,
      })
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '加载失败' })
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [page, keyword, status])

  useEffect(() => {
    load()
  }, [load])

  async function handleDispatch(id) {
    setActionLoading(id)
    try {
      await adminBatch.dispatchJob(id)
      setMessage({ type: 'success', text: '任务已启动' })
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '启动失败' })
    } finally {
      setActionLoading(null)
    }
  }

  async function handlePause(id) {
    setActionLoading(id)
    try {
      await adminBatch.pauseJob(id)
      setMessage({ type: 'success', text: '任务已暂停' })
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '暂停失败' })
    } finally {
      setActionLoading(null)
    }
  }

  async function handleResume(id) {
    setActionLoading(id)
    try {
      await adminBatch.resumeJob(id)
      setMessage({ type: 'success', text: '任务已恢复' })
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '恢复失败' })
    } finally {
      setActionLoading(null)
    }
  }

  const columns = [
    {
      key: 'name',
      title: '任务名称',
      render: (row) => (
        <button
          type="button"
          onClick={() => onSelect(row)}
          className="text-gold-400 hover:text-gold-300 font-medium hover:underline text-left"
        >
          {row.name}
        </button>
      ),
    },
    {
      key: 'theme',
      title: '题材',
      render: (row) => (
        <span className="text-sm text-navy-200">{row.theme || '—'}</span>
      ),
    },
    {
      key: 'status',
      title: '状态',
      render: (row) => <JobStatusBadge status={row.status} />,
    },
    {
      key: 'progress',
      title: '进度',
      render: (row) => {
        const completed = row.completed_count || 0
        const total = row.total_count || 0
        return (
          <div className="flex items-center gap-3">
            <ProgressRing completed={completed} total={total} size={56} />
            <div className="text-xs text-navy-300">
              <div>{completed} / {total}</div>
              <div className="text-navy-400">{total > 0 ? Math.round((completed / total) * 100) : 0}%</div>
            </div>
          </div>
        )
      },
    },
    {
      key: 'created_at',
      title: '创建时间',
      render: (row) => (
        <span className="text-xs text-navy-400 whitespace-nowrap">
          {formatDateTime(row.created_at)}
        </span>
      ),
    },
    {
      key: 'actions',
      title: '操作',
      align: 'right',
      render: (row) => {
        const isLoading = actionLoading === row.id
        return (
          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => onSelect(row)}
              className="inline-flex items-center gap-1 text-xs text-navy-300 hover:text-white"
            >
              <FileText className="w-3.5 h-3.5" />
              详情
            </button>
            {row.status === 'pending' && (
              <button
                type="button"
                disabled={isLoading}
                onClick={() => handleDispatch(row.id)}
                className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                {isLoading ? '启动中…' : '启动'}
              </button>
            )}
            {row.status === 'running' && (
              <button
                type="button"
                disabled={isLoading}
                onClick={() => handlePause(row.id)}
                className="inline-flex items-center gap-1 text-xs text-yellow-400 hover:text-yellow-300 disabled:opacity-50"
              >
                <Pause className="w-3.5 h-3.5" />
                {isLoading ? '暂停中…' : '暂停'}
              </button>
            )}
            {row.status === 'paused' && (
              <button
                type="button"
                disabled={isLoading}
                onClick={() => handleResume(row.id)}
                className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                {isLoading ? '恢复中…' : '恢复'}
              </button>
            )}
          </div>
        )
      },
    },
  ]

  return (
    <div className="space-y-4">
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminToolbar>
        <AdminSearchInput
          value={keyword}
          onChange={(v) => patchParams({ q: v })}
          placeholder="搜索任务名称…"
        />
        <select
          value={status}
          onChange={(e) => patchParams({ status: e.target.value })}
          className="sf-control"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.key} value={o.key}>
              {o.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={load}
          className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-navy-200 hover:bg-white/[0.06]"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </AdminToolbar>

      {loading ? (
        <AdminLoading label="加载批量任务…" />
      ) : (
        <AdminPanel
          title="批量任务"
          sub={`共 ${pagination?.total ?? 0} 个任务`}
        >
          <AdminTable
            rowKey="id"
            rows={items}
            columns={columns}
            emptyText="暂无批量任务"
          />
          <AdminPagination
            page={pagination?.page || 1}
            totalPages={pagination?.total_pages || 1}
            total={pagination?.total}
            onPageChange={(p) => patchParams({ page: p }, false)}
          />
        </AdminPanel>
      )}
    </div>
  )
}

/** 新建批量任务表单 */
function AdminBatchJobCreate({ onCreated, onCancel }) {
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [packs, setPacks] = useState([])
  const [form, setForm] = useState({
    name: '',
    theme: '',
    csv_textarea: '',
    pipeline_pack_id: '',
  })

  useEffect(() => {
    adminWorkflow.listFusionPacks().then((res) => {
      setPacks(res.items || [])
    }).catch(() => null)
  }, [])

  async function handleSubmit() {
    if (!form.name.trim()) {
      setMessage({ type: 'error', text: '请输入任务名称' })
      return
    }
    if (!form.csv_textarea.trim() && !form.pipeline_pack_id) {
      setMessage({ type: 'error', text: '请输入创意内容或选择 Pipeline 包' })
      return
    }

    setLoading(true)
    try {
      const ideas = form.csv_textarea
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
        .map((core_idea) => ({ core_idea }))

      const payload = {
        name: form.name.trim(),
        theme: form.theme || undefined,
        pipeline_pack_id: form.pipeline_pack_id || undefined,
        items: ideas.length > 0 ? ideas : undefined,
      }

      await adminBatch.createJob(payload)
      setMessage({ type: 'success', text: '任务创建成功' })
      onCreated()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '创建失败' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminPanel title="新建批量任务">
        <div className="space-y-4 max-w-2xl">
          <div>
            <label className="block text-sm text-navy-300 mb-1.5">
              任务名称 <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="如：都市情感题材批量创作"
              className="sf-control w-full"
            />
          </div>

          <div>
            <label className="block text-sm text-navy-300 mb-1.5">题材</label>
            <input
              type="text"
              value={form.theme}
              onChange={(e) => setForm((f) => ({ ...f, theme: e.target.value }))}
              placeholder="如：都市情感、悬疑推理、古装玄幻"
              className="sf-control w-full"
            />
          </div>

          <div>
            <label className="block text-sm text-navy-300 mb-1.5">Pipeline 包</label>
            <select
              value={form.pipeline_pack_id}
              onChange={(e) => setForm((f) => ({ ...f, pipeline_pack_id: e.target.value }))}
              className="sf-control w-full"
            >
              <option value="">不指定（使用默认）</option>
              {packs.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.is_active ? '（当前激活）' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-navy-300 mb-1.5">
              核心创意（每行一个）
              <span className="text-navy-500 ml-2">CSV 格式：core_idea 列</span>
            </label>
            <textarea
              rows={10}
              value={form.csv_textarea}
              onChange={(e) => setForm((f) => ({ ...f, csv_textarea: e.target.value }))}
              placeholder={"示例：\n女主意外失忆，被误认为是豪门千金\n穿越回十年前，阻止一场火灾\n快递员卷入一起离奇的失踪案"}
              className="sf-control w-full font-mono text-xs"
              spellCheck={false}
            />
            <p className="text-xs text-navy-500 mt-1">
              每行代表一个创作项目的核心创意，支持批量导入
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 rounded-xl border border-white/10 text-sm text-navy-200 hover:bg-white/[0.06]"
            >
              取消
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={handleSubmit}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-300 text-sm hover:bg-emerald-500/30 disabled:opacity-50"
            >
              {loading ? '创建中…' : '创建任务'}
            </button>
          </div>
        </div>
      </AdminPanel>
    </div>
  )
}

/** 单个子项目行 */
const BatchItemRow = React.memo(function BatchItemRow({ item, batchId, onRetry }) {
  const [expanded, setExpanded] = useState(false)
  const [retrying, setRetrying] = useState(false)

  async function handleRetry() {
    setRetrying(true)
    try {
      await onRetry(batchId, item.id)
    } finally {
      setRetrying(false)
    }
  }

  return (
    <div className="border-b border-white/5 last:border-0">
      <div className="flex items-center gap-3 px-4 py-3 hover:bg-white/[0.02] transition-colors">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-navy-400 hover:text-white"
        >
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>

        <div className="flex-1 min-w-0">
          <p className="text-sm text-white truncate">{item.core_idea || item.title || item.id}</p>
          <p className="text-xs text-navy-400 font-mono mt-0.5">{item.id}</p>
        </div>

        <ItemStatusBadge status={item.status} />

        {item.status === 'failed' && (
          <button
            type="button"
            disabled={retrying}
            onClick={handleRetry}
            className="inline-flex items-center gap-1 text-xs text-orange-400 hover:text-orange-300 disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            {retrying ? '重试中…' : '重试'}
          </button>
        )}

        {item.status === 'running' && (
          <span className="text-xs text-yellow-400">进行中…</span>
        )}
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-8 py-3 bg-white/[0.02] text-xs text-navy-300 space-y-1">
              {item.error_message && (
                <div className="text-red-400">
                  <span className="text-navy-400">错误：</span>
                  {item.error_message}
                </div>
              )}
              {item.started_at && (
                <div>
                  <span className="text-navy-400">开始时间：</span>
                  {formatDateTime(item.started_at)}
                </div>
              )}
              {item.completed_at && (
                <div>
                  <span className="text-navy-400">完成时间：</span>
                  {formatDateTime(item.completed_at)}
                </div>
              )}
              {item.project_id && (
                <div>
                  <span className="text-navy-400">项目ID：</span>
                  <span className="font-mono">{item.project_id}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
})

/** 任务详情页 */
function AdminBatchJobDetail({ job, onBack, onMessage }) {
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState(null)
  const [message, setMessage] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await adminBatch.getJob(job.id)
      setDetail(data)
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '加载详情失败' })
    } finally {
      setLoading(false)
    }
  }, [job.id])

  useEffect(() => {
    load()
  }, [load])

  async function handleRetryItem(batchId, itemId) {
    try {
      await adminBatch.retryItem(batchId, itemId)
      onMessage({ type: 'success', text: '已提交重试' })
      load()
    } catch (e) {
      onMessage({ type: 'error', text: e.message || '重试失败' })
    }
  }

  if (loading) {
    return <AdminLoading label="加载任务详情…" />
  }

  const completed = detail?.completed_count || 0
  const total = detail?.total_count || 0
  const items = detail?.items || []

  return (
    <div className="space-y-4">
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1 text-sm text-navy-400 hover:text-white"
        >
          <ChevronRight className="w-4 h-4 rotate-180" />
          返回列表
        </button>
        <span className="text-navy-600">·</span>
        <span className="text-sm text-gold-400 font-medium">{detail?.name}</span>
        <JobStatusBadge status={detail?.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <AdminPanel title="总进度" className="lg:col-span-1">
          <div className="flex flex-col items-center py-4">
            <ProgressRing completed={completed} total={total} size={100} />
            <div className="mt-3 text-center">
              <div className="text-2xl font-bold text-white">
                {total > 0 ? Math.round((completed / total) * 100) : 0}%
              </div>
              <div className="text-xs text-navy-400">
                {completed} / {total} 项目
              </div>
            </div>
          </div>
        </AdminPanel>

        <AdminPanel title="任务信息" className="lg:col-span-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-navy-400 mb-1">任务名称</div>
              <div className="text-sm text-white">{detail?.name}</div>
            </div>
            <div>
              <div className="text-xs text-navy-400 mb-1">题材</div>
              <div className="text-sm text-white">{detail?.theme || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-navy-400 mb-1">Pipeline</div>
              <div className="text-sm text-navy-200 font-mono">{detail?.pipeline_pack_id || '默认'}</div>
            </div>
            <div>
              <div className="text-xs text-navy-400 mb-1">创建时间</div>
              <div className="text-sm text-navy-300">{formatDateTime(detail?.created_at)}</div>
            </div>
          </div>
        </AdminPanel>
      </div>

      <AdminPanel title="子项目列表" sub={`共 ${items.length} 个项目`}>
        {items.length === 0 ? (
          <div className="py-8 text-center text-navy-400 text-sm">暂无子项目</div>
        ) : (
          <div className="divide-y divide-white/5">
            {items.map((item) => (
              <BatchItemRow
                key={item.id}
                item={item}
                batchId={job.id}
                onRetry={handleRetryItem}
              />
            ))}
          </div>
        )}
      </AdminPanel>
    </div>
  )
}

/** 主组件 */
export default function AdminBatchJobs() {
  const [message, setMessage] = useState(null)
  const [view, setView] = useState('list') // 'list' | 'create' | 'detail'
  const [selectedJob, setSelectedJob] = useState(null)

  function handleSelectJob(job) {
    setSelectedJob(job)
    setView('detail')
  }

  function handleCreated() {
    setView('list')
  }

  function handleBack() {
    setSelectedJob(null)
    setView('list')
  }

  const crumbs = [
    { label: 'Console' },
    { label: '批量创作' },
    ...(view === 'detail' ? [{ label: selectedJob?.name || '任务详情' }] : []),
    ...(view === 'create' ? [{ label: '新建任务' }] : []),
  ]

  return (
    <AdminShell hideDescription>
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminPageHeader
        crumbs={crumbs}
        title="批量创作中心"
        description="CSV 批量生成创作项目 / 进度追踪"
        actions={
          view === 'list' ? (
            <button
              type="button"
              onClick={() => setView('create')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-300 text-sm hover:bg-emerald-500/30"
            >
              <Plus className="w-4 h-4" />
              新建任务
            </button>
          ) : null
        }
      />

      {view === 'list' && (
        <AdminBatchJobList onSelect={handleSelectJob} />
      )}

      {view === 'create' && (
        <AdminBatchJobCreate onCreated={handleCreated} onCancel={() => setView('list')} />
      )}

      {view === 'detail' && selectedJob && (
        <AdminBatchJobDetail
          job={selectedJob}
          onBack={handleBack}
          onMessage={setMessage}
        />
      )}
    </AdminShell>
  )
}
