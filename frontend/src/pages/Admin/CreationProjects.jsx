import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Trash2,
  AlertTriangle,
  Loader2,
  Clock,
  XCircle,
  ListFilter,
  ChevronRight,
} from 'lucide-react'
import { admin } from '@/services/api'
import AdminShell from '@/components/admin/AdminShell'
import AdminDashboardHints from '@/components/admin/AdminDashboardHints'
import { CreationVerifyBadge } from '@/components/admin/ProjectOpsSummary'
import { RunDetailModal } from '@/components/admin/ProjectAgentTrace'
import { formatProjectExecutionSummary } from '@/utils/agentExecutionLabels'
import { adminProjectDetailPath } from '@/utils/adminProjectRoutes'
import {
  AdminToolbar,
  AdminSearchInput,
  AdminTable,
  AdminPagination,
  AdminLoading,
  AdminMessage,
  AdminBadge,
  AdminPageHeader,
  AdminPanel,
  formatDateTime,
} from '@/components/admin/AdminUI'
import ProjectSpotlightCard from '@/components/admin/ProjectSpotlightCard'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const STATUS_OPTIONS = [
  { key: '', label: '全部状态' },
  { key: 'draft', label: '立项中' },
  { key: 'planning', label: '策划中' },
  { key: 'writing', label: '创作中' },
  { key: 'reviewing', label: '质检中' },
  { key: 'scoring', label: '评分中' },
  { key: 'ready', label: '可发布' },
  { key: 'blocked', label: '需修改' },
]

const STATUS_TONE = {
  ready: 'success',
  blocked: 'danger',
  writing: 'warning',
  reviewing: 'warning',
  scoring: 'warning',
  planning: 'default',
  draft: 'default',
}

const MODE_OPTIONS = [
  { key: '', label: '全部模式' },
  { key: 'workspace', label: '工作台' },
  { key: 'auto', label: '一键生成' },
  { key: 'step', label: '分步' },
]

const QUICK_FILTERS = [
  { id: 'all', label: '全部项目', facetKey: 'all', icon: ListFilter },
  { id: 'running', label: '创作中', facetKey: 'running', icon: Loader2, status: 'writing' },
  { id: 'failed', label: '需修改', facetKey: 'failed', icon: XCircle, status: 'blocked' },
  { id: 'awaiting', label: '质检中', facetKey: 'awaiting', icon: Clock, status: 'reviewing' },
  {
    id: 'failed_run',
    label: '有失败 run',
    facetKey: 'has_failed_run',
    icon: AlertTriangle,
    failedRun: true,
  },
]

function activeQuickFilterId(status, hasFailedRun) {
  if (hasFailedRun) return 'failed_run'
  if (status === 'writing') return 'running'
  if (status === 'blocked') return 'failed'
  if (status === 'reviewing') return 'awaiting'
  if (!status) return 'all'
  return ''
}

function isProjectBusy(status) {
  return ['writing', 'reviewing', 'scoring', 'planning'].includes(status)
}

export default function CreationProjectsPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [inspectRunId, setInspectRunId] = useState(null)

  const keyword = searchParams.get('q') || ''
  const status = searchParams.get('status') || ''
  const pipelineMode = searchParams.get('mode') || ''
  const hasFailedRun = searchParams.get('failed_run') === '1'
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10) || 1)

  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState(null)
  const [facets, setFacets] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [agentCatalog, setAgentCatalog] = useState(null)

  const openProject = useCallback(
    (projectId, tab = 'basic') => {
      navigate(adminProjectDetailPath(projectId, tab))
    },
    [navigate],
  )

  useEffect(() => {
    admin.agentCatalog().then(setAgentCatalog).catch(() => null)
  }, [])

  const patchParams = useCallback(
    (patch, resetPage = true) => {
      const next = new URLSearchParams(searchParams)
      Object.entries(patch).forEach(([key, value]) => {
        if (value === '' || value === false || value == null) {
          next.delete(key)
        } else if (value === true) {
          next.set(key, '1')
        } else {
          next.set(key, String(value))
        }
      })
      if (resetPage) next.delete('page')
      setSearchParams(next, { replace: true })
    },
    [searchParams, setSearchParams],
  )

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await admin.listCreationProjects({
        page,
        page_size: 20,
        facets: '1',
        keyword: keyword.trim() || undefined,
        status: status || undefined,
        pipeline_mode: pipelineMode || undefined,
        has_failed_run: hasFailedRun ? 'true' : undefined,
      })
      const pageInfo = res.pagination
      setItems(res.items)
      setFacets(res.facets || null)
      setPagination({
        page: pageInfo.page,
        total_pages: pageInfo.total_pages,
        total: pageInfo.total,
        page_size: pageInfo.page_size,
      })
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '加载失败' })
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [page, keyword, status, pipelineMode, hasFailedRun])

  useEffect(() => {
    load()
    const timer = setInterval(() => { load() }, 10_000)
    return () => clearInterval(timer)
  }, [load])

  const quickActive = useMemo(
    () => activeQuickFilterId(status, hasFailedRun),
    [status, hasFailedRun],
  )

  const spotlightProjects = useMemo(() => {
    if (!items?.length) return []
    const running = items.find((p) => p.status === 'writing')
    const completed = items.find((p) => p.status === 'ready')
    const picked = []
    if (running) picked.push(running)
    if (completed && completed.project_id !== running?.project_id) picked.push(completed)
    if (picked.length < 2) {
      for (const p of items) {
        if (picked.length >= 2) break
        if (!picked.some((x) => x.project_id === p.project_id)) picked.push(p)
      }
    }
    return picked.slice(0, 2)
  }, [items])

  const runningCount = facets?.running ?? pagination?.total ?? items.length

  const applyQuickFilter = (filter) => {
    patchParams({
      status: filter.status || '',
      failed_run: filter.failedRun ? true : false,
      mode: '',
      q: keyword || '',
    })
  }

  const handleDelete = async (row, event) => {
    event?.stopPropagation?.()
    const title = row.title || row.project_id
    if (isProjectBusy(row.status)) {
      setMessage({ type: 'error', text: '该项目仍在进行中，请等待完成或进入需修改状态后再删除。' })
      return
    }
    if (!window.confirm(`确定删除「${title}」？\n将同时删除剧本、大纲、分享链接等全部数据，且无法恢复。`)) return
    setDeletingId(row.project_id)
    try {
      await admin.deleteCreationProject(row.project_id)
      setItems((prev) => prev.filter((p) => p.project_id !== row.project_id))
      setPagination((prev) => ({
        ...prev,
        total: Math.max(0, (prev?.total || 1) - 1),
      }))
      setMessage({ type: 'success', text: '项目已删除' })
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '删除失败' })
    } finally {
      setDeletingId(null)
    }
  }

  const columns = [
    {
      key: 'title',
      title: '项目',
      render: (row) => (
        <div className="min-w-[160px]">
          <p className="text-white font-medium truncate max-w-[240px]">{row.title}</p>
          <p className="text-xs text-navy-300 font-mono mt-0.5">{row.project_id}</p>
        </div>
      ),
    },
    {
      key: 'user',
      title: '用户',
      render: (row) => (
        <span className="text-navy-200 text-xs">{row.user_phone || row.user_id || '—'}</span>
      ),
    },
    {
      key: 'status',
      title: '状态',
      render: (row) => (
        <div className="space-y-1">
          <AdminBadge tone={STATUS_TONE[row.status] || 'default'}>
            {row.status_text || row.status}
          </AdminBadge>
          <p className="text-[10px] text-navy-400">{row.pipeline_mode}</p>
        </div>
      ),
    },
    {
      key: 'entry',
      title: '入口',
      render: (row) => (
        <span className="text-xs text-navy-300">{row.creation_entry || '—'}</span>
      ),
    },
    {
      key: 'execution',
      title: '最近执行',
      render: (row) => {
        const failed = row.latest_failed_run
        const latest = row.latest_execution_run
        const target = failed || latest
        if (!target) {
          return <span className="text-navy-400 text-xs">尚无执行记录</span>
        }
        const summary = formatProjectExecutionSummary(target, agentCatalog)
        return (
          <div className="text-xs space-y-1 min-w-[160px]">
            <p
              className={
                summary.tone === 'danger'
                  ? 'text-red-300 font-medium'
                  : summary.tone === 'success'
                    ? 'text-green-400'
                    : 'text-navy-200'
              }
            >
              {summary.primary}
            </p>
            <p className="text-navy-400 line-clamp-2">{summary.secondary}</p>
            {row.execution_failed_count > 0 ? (
              <p className="text-[10px] text-red-400/80">累计失败 {row.execution_failed_count} 次</p>
            ) : null}
          </div>
        )
      },
    },
    {
      key: 'agent',
      title: '复核',
      render: (row) => (
        <div className="text-xs">
          <CreationVerifyBadge summary={row.verify_summary} />
          {row.has_agent_traces ? (
            <p className="text-[10px] text-navy-400 mt-1">artifact 轨迹 {row.trace_agent_count} 组</p>
          ) : null}
        </div>
      ),
    },
    {
      key: 'score',
      title: '评分',
      render: (row) =>
        row.overall_score != null ? (
          <span className="text-gold-400 text-sm">
            {row.overall_score}
            {row.grade ? ` · ${row.grade}` : ''}
          </span>
        ) : (
          <span className="text-navy-400">—</span>
        ),
    },
    {
      key: 'time',
      title: '更新',
      render: (row) => (
        <span className="text-xs text-navy-400 whitespace-nowrap">
          {formatDateTime(row.updated_at)}
        </span>
      ),
    },
    {
      key: 'actions',
      title: '',
      render: (row) => {
        const isDeleting = deletingId === row.project_id
        const busy = isProjectBusy(row.status)
        return (
          <div className="flex items-center gap-2">
            <ChevronRight className="w-4 h-4 text-gold-400/80" />
            <button
              type="button"
              disabled={isDeleting || busy}
              onClick={(e) => handleDelete(row, e)}
              className="inline-flex items-center gap-1 text-xs text-red-400 hover:text-red-300 disabled:opacity-40"
              title={busy ? '进行中不可删除' : '删除项目'}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        )
      },
    },
  ]

  return (
    <AdminShell hideDescription actions={<AdminDashboardHints scope="creation" />}>
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminPageHeader
        crumbs={[{ label: 'Console' }, { label: '创作项目' }]}
        title={`创作项目 · ${runningCount ?? 0} 进行中`}
        subtitle="点击任意项目进入详情工作台（基本信息 / 执行记录 / AI 产物 / 质量缺陷）"
      />

      {spotlightProjects.length > 0 ? (
        <div className="mb-5 grid grid-cols-1 gap-3.5 lg:grid-cols-2">
          {spotlightProjects.map((p) => (
            <ProjectSpotlightCard
              key={p.project_id}
              project={{
                ...p,
                current_node: p.current_step || p.current_node || 1,
                elapsed: p.elapsed_text,
                remain: p.remain_text,
              }}
              onTrace={() => openProject(p.project_id, 'timeline')}
              onFullTrace={() => openProject(p.project_id, 'basic')}
              onIntervene={() => openProject(p.project_id, rowHasFailedRun(p) ? 'runs' : 'basic')}
            />
          ))}
        </div>
      ) : null}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {QUICK_FILTERS.map((filter) => {
          const active = quickActive === filter.id
          const count = facets?.[filter.facetKey]
          return (
            <button
              key={filter.id}
              type="button"
              onClick={() => applyQuickFilter(filter)}
              className={`rounded-2xl border p-4 text-left transition-all ${
                active
                  ? 'border-gold-500/40 bg-gold-500/10 ring-1 ring-gold-500/25'
                  : 'border-white/10 bg-white/[0.03] hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                {renderLucideIcon(filter.icon, `w-4 h-4 ${active ? 'text-gold-400' : 'text-navy-400'}`)}
                <span className={`text-xl font-bold ${active ? 'text-gold-300' : 'text-white'}`}>
                  {count != null ? count : '—'}
                </span>
              </div>
              <p className={`text-xs ${active ? 'text-gold-200' : 'text-navy-400'}`}>
                {filter.label}
              </p>
            </button>
          )
        })}
      </div>

      <AdminToolbar>
        <AdminSearchInput
          value={keyword}
          onChange={(v) => patchParams({ q: v })}
          placeholder="标题 / 题材 / 用户手机…"
        />
        <select
          value={status}
          onChange={(e) => patchParams({ status: e.target.value, failed_run: false })}
          className="sf-control"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.key || 'all'} value={o.key}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          value={pipelineMode}
          onChange={(e) => patchParams({ mode: e.target.value })}
          className="sf-control"
        >
          {MODE_OPTIONS.map((o) => (
            <option key={o.key || 'all'} value={o.key}>
              {o.label}
            </option>
          ))}
        </select>
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-navy-200">
          <input
            type="checkbox"
            checked={hasFailedRun}
            onChange={(e) =>
              patchParams({
                failed_run: e.target.checked,
                status: e.target.checked ? '' : status,
              })
            }
            className="rounded border-white/20"
          />
          仅有失败 run
        </label>
      </AdminToolbar>

      {loading ? (
        <AdminLoading label="加载项目…" />
      ) : (
        <AdminPanel
          title="全部项目"
          sub={`点击行进入详情 · 共 ${pagination?.total ?? 0}${keyword ? ` · 搜索「${keyword}」` : ''}`}
        >
          <AdminTable
            columns={columns}
            rows={items}
            rowKey="project_id"
            emptyText="暂无创作项目"
            onRowClick={(row) => openProject(row.project_id, row.latest_failed_run ? 'runs' : 'basic')}
          />
          <AdminPagination
            page={pagination?.page || 1}
            totalPages={pagination?.total_pages || 1}
            total={pagination?.total}
            onPageChange={(p) => patchParams({ page: p }, false)}
          />
        </AdminPanel>
      )}

      <RunDetailModal runId={inspectRunId} onClose={() => setInspectRunId(null)} />
    </AdminShell>
  )
}

function rowHasFailedRun(row) {
  return (row.execution_failed_count ?? 0) > 0 || Boolean(row.latest_failed_run)
}
