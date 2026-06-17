/**
 * pages/Admin/operations/FeedbackPage.jsx
 *
 * 【运营 F5】用户反馈管理：列表 + 处理 + 抽样回访
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { RefreshCw, Search, ChevronRight, Check, X, AlertTriangle } from 'lucide-react'

import AdminShell from '@/components/admin/AdminShell'
import { Button, EmptyState, Skeleton } from '@/components/ui'
import { useToast } from '@/hooks/useToast'
import { adminOperations } from '@/services/admin'

const STATUS_LABELS = {
  open: '待处理',
  in_progress: '处理中',
  resolved: '已处理',
  wont_fix: '不处理',
}
const CATEGORY_LABELS = {
  feature_request: '功能建议',
  bug: 'BUG',
  consult: '咨询',
  praise: '表扬',
  complaint: '投诉',
  other: '其它',
}
const SEVERITY_LABELS = { P0: 'P0', P1: 'P1', P2: 'P2', P3: 'P3' }
const SEVERITY_TONE = {
  P0: 'bg-danger-500/20 text-danger-200',
  P1: 'bg-warning-500/20 text-warning-200',
  P2: 'bg-info-500/20 text-info-200',
  P3: 'bg-slate-700/40 text-navy-300',
}

export default function FeedbackPage() {
  const { toast } = useToast()
  const [filters, setFilters] = useState({ status: '', category: '', severity: '', keyword: '', p0_only: false, page: 1 })
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page: filters.page, page_size: 20, facets: 1 }
      if (filters.status) params.status = filters.status
      if (filters.category) params.category = filters.category
      if (filters.severity) params.severity = filters.severity
      if (filters.keyword) params.keyword = filters.keyword
      if (filters.p0_only) params.p0_only = 1
      const res = await adminOperations.feedback.list(params)
      setData(res)
    } catch (e) {
      setError(e?.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    load()
  }, [load])

  const facets = data?.facets || null
  const items = data?.items || []
  const pagination = data?.pagination || { page: 1, page_size: 20, total: 0, total_pages: 0 }

  const handlePatch = useCallback(async (id, payload, successMsg) => {
    try {
      await adminOperations.feedback.patch(id, payload)
      toast.success(successMsg || '已更新')
      load()
    } catch (e) {
      toast.error(e?.message || '操作失败')
    }
  }, [load, toast])

  return (
    <AdminShell
      title="用户反馈"
      description="一人运营工单台：P0 优先看，按分类汇总"
      actions={
        <Button variant="secondary" onClick={load} icon={<RefreshCw className="h-4 w-4" />}>
          刷新
        </Button>
      }
    >
      {/* Facets */}
      {facets ? (
        <section className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-5">
          {[
            { key: 'all', label: '总反馈', value: facets.all, tone: 'text-white' },
            { key: 'open', label: '待处理', value: facets.open, tone: 'text-warning-300' },
            { key: 'in_progress', label: '处理中', value: facets.in_progress, tone: 'text-info-300' },
            { key: 'resolved', label: '已处理', value: facets.resolved, tone: 'text-success-300' },
            { key: 'p0_open', label: 'P0 未关闭', value: facets.p0_open, tone: 'text-danger-300' },
          ].map((f) => (
            <div key={f.key} className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
              <p className="text-xs text-navy-400">{f.label}</p>
              <p className={`mt-1 text-2xl font-bold ${f.tone}`}>{f.value ?? 0}</p>
            </div>
          ))}
        </section>
      ) : null}

      {/* 筛选 */}
      <section className="sf-toolbar mb-4 rounded-2xl border border-white/10 bg-slate-900/60 p-4">
        <div className="sf-toolbar-search flex items-center gap-2">
          <Search className="h-4 w-4 shrink-0 text-navy-400" />
          <input
            value={filters.keyword}
            onChange={(e) => setFilters((f) => ({ ...f, keyword: e.target.value, page: 1 }))}
            placeholder="搜索标题/正文"
            className="sf-control h-11 min-w-0 flex-1 border-0 bg-transparent p-0 focus:ring-0"
          />
        </div>
        <select
          value={filters.status}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value, page: 1 }))}
          className="sf-control w-32"
        >
          <option value="">全部状态</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          value={filters.category}
          onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value, page: 1 }))}
          className="sf-control w-32"
        >
          <option value="">全部分类</option>
          {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          value={filters.severity}
          onChange={(e) => setFilters((f) => ({ ...f, severity: e.target.value, page: 1 }))}
          className="sf-control w-28"
        >
          <option value="">全部等级</option>
          {Object.entries(SEVERITY_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <label className="flex items-center gap-1 text-xs text-navy-300">
          <input
            type="checkbox"
            checked={filters.p0_only}
            onChange={(e) => setFilters((f) => ({ ...f, p0_only: e.target.checked, page: 1 }))}
          />
          只看 P0
        </label>
      </section>

      {error ? <EmptyState title="加载失败" description={error} actionLabel="重试" onAction={load} /> : null}

      {loading && !data ? (
        <Skeleton className="h-72" />
      ) : items.length === 0 ? (
        <EmptyState title="暂无反馈" description="用户还没有提交任何反馈" />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-900/60">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-left text-xs text-navy-400">
                <th className="px-3 py-3">等级</th>
                <th className="px-3 py-3">分类</th>
                <th className="px-3 py-3">标题 / 用户</th>
                <th className="px-3 py-3">来源</th>
                <th className="px-3 py-3">状态</th>
                <th className="px-3 py-3">提交时间</th>
                <th className="px-3 py-3">操作</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} className="border-b border-white/5 hover:bg-slate-800/40">
                  <td className="px-3 py-2">
                    <span className={`rounded px-2 py-0.5 text-[11px] font-semibold ${SEVERITY_TONE[it.severity] || ''}`}>
                      {it.severity}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-navy-200">{it.category_display}</td>
                  <td className="px-3 py-2">
                    <p className="text-navy-100">{it.title}</p>
                    <p className="text-[11px] text-navy-500">
                      {it.user_nickname} · {it.project_title || '无项目'}
                    </p>
                    {it.handler_note ? (
                      <p className="mt-1 text-[11px] text-warning-300">备注：{it.handler_note}</p>
                    ) : null}
                  </td>
                  <td className="px-3 py-2 text-navy-300">{it.source_display}</td>
                  <td className="px-3 py-2 text-navy-200">{it.status_display}</td>
                  <td className="px-3 py-2 text-navy-400">
                    {it.created_at ? new Date(it.created_at).toLocaleString('zh-CN', { hour12: false }) : '—'}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-1">
                      {it.status === 'open' ? (
                        <Button
                          size="xs"
                          variant="secondary"
                          onClick={() => handlePatch(it.id, { status: 'in_progress' }, '已开始处理')}
                        >
                          接手
                        </Button>
                      ) : null}
                      {it.status !== 'resolved' ? (
                        <Button
                          size="xs"
                          variant="primary"
                          onClick={() => handlePatch(it.id, { status: 'resolved' }, '已标记为已处理')}
                        >
                          <Check className="h-3 w-3" />
                        </Button>
                      ) : null}
                      {it.status !== 'wont_fix' ? (
                        <Button
                          size="xs"
                          variant="ghost"
                          onClick={() => handlePatch(it.id, { status: 'wont_fix' }, '已标记为不处理')}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 分页 */}
      {pagination.total_pages > 1 ? (
        <div className="mt-4 flex items-center justify-center gap-2 text-xs text-navy-300">
          <Button
            size="xs"
            variant="ghost"
            disabled={pagination.page <= 1}
            onClick={() => setFilters((f) => ({ ...f, page: Math.max(1, f.page - 1) }))}
          >
            上一页
          </Button>
          <span>
            {pagination.page} / {pagination.total_pages}（共 {pagination.total}）
          </span>
          <Button
            size="xs"
            variant="ghost"
            disabled={pagination.page >= pagination.total_pages}
            onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}
          >
            下一页
          </Button>
        </div>
      ) : null}
    </AdminShell>
  )
}
