import React, { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  RefreshCw,
  Play,
  ChevronRight,
  ChevronDown,
  CheckCircle,
  XCircle,
  Zap,
  Clock,
  AlertTriangle,
} from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { adminEvolution } from '@/services/admin/evolution'
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
  { key: 'pending', label: '待审批' },
  { key: 'approved', label: '已批准' },
  { key: 'rejected', label: '已拒绝' },
  { key: 'applied', label: '已应用' },
]

const STATUS_TONE = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  applied: 'default',
}

const STATUS_LABEL = {
  pending: '待审批',
  approved: '已批准',
  rejected: '已拒绝',
  applied: '已应用',
}

const TIME_RANGE_OPTIONS = [
  { key: 7, label: '近 7 天' },
  { key: 14, label: '近 14 天' },
  { key: 30, label: '近 30 天' },
]

function ProposalStatusBadge({ status }) {
  return (
    <AdminBadge tone={STATUS_TONE[status] || 'default'}>
      {STATUS_LABEL[status] || status}
    </AdminBadge>
  )
}

/** 触发分析弹窗 */
function AnalyzeDialog({ open, onClose, onAnalyze }) {
  const [timeRange, setTimeRange] = useState(7)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)

  async function handleAnalyze() {
    setLoading(true)
    try {
      await onAnalyze({ days: timeRange })
      setMessage({ type: 'success', text: '分析完成，已生成提案' })
      onClose()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '分析失败' })
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  return (
    <motion.div
      {...modalOverlay}
      className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-navy-950/80 backdrop-blur-sm"
    >
      <motion.div
        {...modalPanel}
        className="sf-console-panel p-6 max-w-md w-full shadow-modal"
      >
        <AdminMessage message={message} onClose={() => setMessage(null)} />

        <div className="flex items-start gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gold-500/15 flex items-center justify-center flex-shrink-0">
            <Zap className="w-5 h-5 text-gold-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">触发 AI 分析</h3>
            <p className="text-sm text-navy-300 mt-1">
              AI 将分析低评分项目，自动生成规则修改提案
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-navy-300 mb-2">分析时间范围</label>
            <div className="flex gap-2">
              {TIME_RANGE_OPTIONS.map((opt) => (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => setTimeRange(opt.key)}
                  className={cn(
                    'flex-1 px-3 py-2 rounded-xl border text-sm transition-all',
                    timeRange === opt.key
                      ? 'border-gold-500/40 bg-gold-400/10 text-gold-200'
                      : 'border-white/10 text-navy-300 hover:bg-white/[0.04]'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-start gap-2 rounded-lg border border-yellow-500/20 bg-yellow-500/10 p-3">
            <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-yellow-300">
              分析过程可能需要几分钟，完成后将生成新的提案列表。
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl border border-white/10 text-sm text-navy-200 hover:bg-white/[0.06]"
          >
            取消
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={handleAnalyze}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm hover:bg-gold-400/30 disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                分析中…
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                开始分析
              </>
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

/** 审批评论弹窗 */
function ApprovalDialog({ open, title, confirmText, onClose, onConfirm }) {
  const [comment, setComment] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleConfirm() {
    setLoading(true)
    try {
      await onConfirm(comment)
      onClose()
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  return (
    <motion.div
      {...modalOverlay}
      className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-navy-950/80 backdrop-blur-sm"
    >
      <motion.div
        {...modalPanel}
        className="sf-console-panel p-6 max-w-md w-full shadow-modal"
      >
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-navy-300 mb-1.5">审批意见（可选）</label>
            <textarea
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="输入审批意见..."
              className="sf-control w-full text-sm"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl border border-white/10 text-sm text-navy-200 hover:bg-white/[0.06]"
          >
            取消
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={handleConfirm}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm hover:bg-gold-400/30 disabled:opacity-50"
          >
            {loading ? '处理中…' : confirmText}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

/** 提案详情对比视图 */
function ProposalDetailView({ proposal, onBack, onApprove, onReject, onApply, actionLoading }) {
  const [expanded, setExpanded] = useState({})

  function toggleSection(key) {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  if (!proposal) return null

  return (
    <div className="space-y-4">
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
        <span className="text-sm text-gold-400 font-medium">提案 #{proposal.id}</span>
        <ProposalStatusBadge status={proposal.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AdminPanel title="提案信息">
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-navy-400">目标技能</span>
              <span className="text-white">{proposal.target_skill || proposal.skill_name || '—'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-navy-400">分析维度</span>
              <span className="text-white">{proposal.dimension || proposal.rule_type || '—'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-navy-400">提案时间</span>
              <span className="text-navy-300">{formatDateTime(proposal.created_at)}</span>
            </div>
            {proposal.approved_by && (
              <div className="flex items-center justify-between">
                <span className="text-navy-400">审批人</span>
                <span className="text-navy-200">{proposal.approved_by}</span>
              </div>
            )}
            {proposal.approved_at && (
              <div className="flex items-center justify-between">
                <span className="text-navy-400">审批时间</span>
                <span className="text-navy-300">{formatDateTime(proposal.approved_at)}</span>
              </div>
            )}
          </div>
        </AdminPanel>

        <AdminPanel title="修改理由">
          <p className="text-sm text-navy-200 leading-relaxed">
            {proposal.reason || proposal.modification_reason || '暂无说明'}
          </p>
        </AdminPanel>
      </div>

      {/* 当前值 vs 提案值 */}
      <AdminPanel title="规则修改对比">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full bg-red-400" />
              <span className="text-sm font-medium text-red-300">当前值</span>
            </div>
            <div className="font-mono text-xs text-navy-300 bg-navy-950/50 rounded-lg p-3 overflow-x-auto">
              <pre className="whitespace-pre-wrap">
                {proposal.current_value != null
                  ? typeof proposal.current_value === 'object'
                    ? JSON.stringify(proposal.current_value, null, 2)
                    : String(proposal.current_value)
                  : '—'}
              </pre>
            </div>
          </div>

          <div className="rounded-xl border border-gold-500/20 bg-gold-400/[0.02] p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-sm font-medium text-emerald-300">提案值</span>
            </div>
            <div className="font-mono text-xs text-navy-300 bg-navy-950/50 rounded-lg p-3 overflow-x-auto">
              <pre className="whitespace-pre-wrap">
                {proposal.proposed_value != null
                  ? typeof proposal.proposed_value === 'object'
                    ? JSON.stringify(proposal.proposed_value, null, 2)
                    : String(proposal.proposed_value)
                  : '—'}
              </pre>
            </div>
          </div>
        </div>
      </AdminPanel>

      {/* 审批操作 */}
      {proposal.status === 'pending' && (
        <div className="flex justify-end gap-3">
          <button
            type="button"
            disabled={actionLoading}
            onClick={() => onReject(proposal.id)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-red-500/30 text-red-400 text-sm hover:bg-red-500/10 disabled:opacity-50"
          >
            <XCircle className="w-4 h-4" />
            {actionLoading ? '拒绝中…' : '拒绝'}
          </button>
          <button
            type="button"
            disabled={actionLoading}
            onClick={() => onApprove(proposal.id)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-emerald-500/30 text-emerald-400 text-sm hover:bg-emerald-500/10 disabled:opacity-50"
          >
            <CheckCircle className="w-4 h-4" />
            {actionLoading ? '批准中…' : '批准'}
          </button>
        </div>
      )}

      {proposal.status === 'approved' && (
        <div className="flex justify-end">
          <button
            type="button"
            disabled={actionLoading}
            onClick={() => onApply(proposal.id)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/20 text-blue-300 text-sm hover:bg-blue-500/30 disabled:opacity-50"
          >
            <Zap className="w-4 h-4" />
            {actionLoading ? '应用中…' : '应用规则'}
          </button>
        </div>
      )}
    </div>
  )
}

/** 提案列表 */
function ProposalList({ onSelect }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState(null)
  const [actionLoading, setActionLoading] = useState(null)

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
      const res = await adminEvolution.listProposals({
        page,
        page_size: 20,
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
  }, [page, status])

  useEffect(() => {
    load()
  }, [load])

  const columns = [
    {
      key: 'id',
      title: '提案ID',
      render: (row) => (
        <span className="text-xs text-gold-400 font-mono">#{row.id}</span>
      ),
    },
    {
      key: 'target_skill',
      title: '目标技能',
      render: (row) => (
        <span className="text-sm text-white">{row.target_skill || row.skill_name || '—'}</span>
      ),
    },
    {
      key: 'dimension',
      title: '分析维度',
      render: (row) => (
        <span className="text-xs text-navy-300">{row.dimension || row.rule_type || '—'}</span>
      ),
    },
    {
      key: 'status',
      title: '状态',
      render: (row) => <ProposalStatusBadge status={row.status} />,
    },
    {
      key: 'reason',
      title: '修改理由',
      render: (row) => (
        <span className="text-xs text-navy-300 line-clamp-2 max-w-[200px]">
          {row.reason || row.modification_reason || '—'}
        </span>
      ),
    },
    {
      key: 'approved_by',
      title: '审批人',
      render: (row) => (
        <span className="text-xs text-navy-400">{row.approved_by || '—'}</span>
      ),
    },
    {
      key: 'created_at',
      title: '提案时间',
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
      render: (row) => (
        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={() => onSelect(row)}
            className="inline-flex items-center gap-1 text-xs text-navy-300 hover:text-white"
          >
            查看详情
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminToolbar>
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
        <AdminLoading label="加载提案…" />
      ) : (
        <AdminPanel
          title="提案列表"
          sub={`共 ${pagination?.total ?? 0} 个提案`}
        >
          <AdminTable
            rowKey="id"
            rows={items}
            columns={columns}
            emptyText="暂无提案"
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

/** 主组件 */
export default function AdminEvolution() {
  const [message, setMessage] = useState(null)
  const [view, setView] = useState('list') // 'list' | 'detail'
  const [selectedProposal, setSelectedProposal] = useState(null)
  const [analyzeDialogOpen, setAnalyzeDialogOpen] = useState(false)
  const [approveDialogOpen, setApproveDialogOpen] = useState(false)
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)

  function handleSelectProposal(proposal) {
    setSelectedProposal(proposal)
    setView('detail')
  }

  function handleBack() {
    setSelectedProposal(null)
    setView('list')
  }

  async function handleAnalyze(data) {
    await adminEvolution.analyze(data)
    setMessage({ type: 'success', text: 'AI 分析完成，已生成提案' })
  }

  async function handleApprove(id, comment) {
    setActionLoading(true)
    try {
      await adminEvolution.approve(id, comment)
      setMessage({ type: 'success', text: '提案已批准' })
      setApproveDialogOpen(false)
      if (view === 'detail') {
        // 刷新详情
        const updated = await adminEvolution.getProposal(id)
        setSelectedProposal(updated)
      }
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '批准失败' })
    } finally {
      setActionLoading(false)
    }
  }

  async function handleReject(id, comment) {
    setActionLoading(true)
    try {
      await adminEvolution.reject(id, comment)
      setMessage({ type: 'success', text: '提案已拒绝' })
      setRejectDialogOpen(false)
      if (view === 'detail') {
        const updated = await adminEvolution.getProposal(id)
        setSelectedProposal(updated)
      }
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '拒绝失败' })
    } finally {
      setActionLoading(false)
    }
  }

  async function handleApply(id) {
    setActionLoading(true)
    try {
      await adminEvolution.apply(id)
      setMessage({ type: 'success', text: '规则已应用' })
      const updated = await adminEvolution.getProposal(id)
      setSelectedProposal(updated)
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '应用失败' })
    } finally {
      setActionLoading(false)
    }
  }

  const crumbs = [
    { label: 'Console' },
    { label: '规则进化' },
    ...(view === 'detail' ? [{ label: `提案 #${selectedProposal?.id || ''}` }] : []),
  ]

  return (
    <AdminShell hideDescription>
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminPageHeader
        crumbs={crumbs}
        title="AI 规则进化"
        description="AI 分析低评分项目 / 生成规则修改提案 / 审批流"
        actions={
          view === 'list' ? (
            <button
              type="button"
              onClick={() => setAnalyzeDialogOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm hover:bg-gold-400/30"
            >
              <Zap className="w-4 h-4" />
              触发分析
            </button>
          ) : null
        }
      />

      {view === 'list' && (
        <ProposalList onSelect={handleSelectProposal} />
      )}

      {view === 'detail' && selectedProposal && (
        <ProposalDetailView
          proposal={selectedProposal}
          onBack={handleBack}
          onApprove={(id) => setApproveDialogOpen(true)}
          onReject={(id) => setRejectDialogOpen(true)}
          onApply={handleApply}
          actionLoading={actionLoading}
        />
      )}

      <AnalyzeDialog
        open={analyzeDialogOpen}
        onClose={() => setAnalyzeDialogOpen(false)}
        onAnalyze={handleAnalyze}
      />

      <ApprovalDialog
        open={approveDialogOpen}
        title="批准提案"
        confirmText="确认批准"
        onClose={() => setApproveDialogOpen(false)}
        onConfirm={(comment) => handleApprove(selectedProposal?.id, comment)}
      />

      <ApprovalDialog
        open={rejectDialogOpen}
        title="拒绝提案"
        confirmText="确认拒绝"
        onClose={() => setRejectDialogOpen(false)}
        onConfirm={(comment) => handleReject(selectedProposal?.id, comment)}
      />
    </AdminShell>
  )
}
