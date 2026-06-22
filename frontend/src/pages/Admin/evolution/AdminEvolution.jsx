import React, { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  RefreshCw,
  Play,
  CheckCircle,
  XCircle,
  Zap,
  AlertTriangle,
} from 'lucide-react'
import AiConfigShell from '@/components/admin/ai-config/AiConfigShell'
import { adminEvolution } from '@/services/admin/evolution'
import {
  AdminLoading,
  AdminMessage,
  AdminBadge,
  AdminPanel,
  AdminConfirmDialog,
  formatDateTime,
} from '@/components/admin/AdminUI'
import { modalOverlay, modalPanel } from '@/constants/motion'
import { cn } from '@/utils/cn'
import { adminProjectDetailPath } from '@/utils/adminProjectRoutes'
import {
  AdminPenetrationLink,
  AdminWorkbench,
  adminBtnSecondary,
} from '@/components/admin/workbench/AdminWorkbenchKit'

const STATUS_OPTIONS = [
  { key: '', label: '全部状态' },
  { key: 'draft', label: '草稿' },
  { key: 'pending_approval', label: '待审批' },
  { key: 'approved', label: '已批准' },
  { key: 'rejected', label: '已拒绝' },
  { key: 'applied', label: '已应用' },
]

const STATUS_TONE = {
  draft: 'default',
  pending_approval: 'warning',
  approved: 'success',
  rejected: 'danger',
  applied: 'default',
}

const STATUS_LABEL = {
  draft: '草稿',
  pending_approval: '待审批',
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
function ProposalDetailView({ proposal, onApprove, onReject, onApply, actionLoading }) {
  if (!proposal) return null

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AdminPanel title="提案信息">
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-navy-400">触发项目</span>
              {proposal.trigger_project_id ? (
                <AdminPenetrationLink
                  to={adminProjectDetailPath(proposal.trigger_project_id, 'quality')}
                  label="查看项目"
                />
              ) : (
                <span className="text-navy-500">—</span>
              )}
            </div>
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
      {proposal.status === 'pending_approval' && (
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

/** 主组件 */
export default function AdminEvolution({ embedded = false, filterSkillId }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [selectedProposal, setSelectedProposal] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [analyzeDialogOpen, setAnalyzeDialogOpen] = useState(false)
  const [approveDialogOpen, setApproveDialogOpen] = useState(false)
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)

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
    [searchParams, setSearchParams],
  )

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await adminEvolution.listProposals({
        page,
        page_size: 20,
        status: status || undefined,
      })
      const rows = (res.items || []).filter((row) => {
        if (!filterSkillId) return true
        const skill = row.target_skill || row.skill_name || ''
        return skill === filterSkillId
      })
      setItems(rows)
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
  }, [page, status, filterSkillId])

  useEffect(() => {
    load()
  }, [load])

  async function handleSelectProposal(id) {
    setSelectedId(id)
    setDetailLoading(true)
    try {
      const detail = await adminEvolution.getProposal(id)
      setSelectedProposal(detail)
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '加载提案详情失败' })
      setSelectedProposal(null)
    } finally {
      setDetailLoading(false)
    }
  }

  async function handleAnalyze(data) {
    await adminEvolution.analyze(data)
    setMessage({ type: 'success', text: 'AI 分析完成，已生成提案' })
    load()
  }

  async function handleApprove(id, comment) {
    setActionLoading(true)
    try {
      await adminEvolution.approve(id, comment)
      setMessage({ type: 'success', text: '提案已批准' })
      setApproveDialogOpen(false)
      const updated = await adminEvolution.getProposal(id)
      setSelectedProposal(updated)
      load()
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
      const updated = await adminEvolution.getProposal(id)
      setSelectedProposal(updated)
      load()
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
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '应用失败' })
    } finally {
      setActionLoading(false)
    }
  }

  const toolbar = (
    <div className="flex flex-wrap items-center gap-3">
      <select
        value={status}
        onChange={(e) => patchParams({ status: e.target.value })}
        className="sf-control text-sm min-w-[140px]"
      >
        {STATUS_OPTIONS.map((o) => (
          <option key={o.key} value={o.key}>
            {o.label}
          </option>
        ))}
      </select>
      <button type="button" onClick={load} className={adminBtnSecondary()}>
        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        刷新
      </button>
      <span className="text-xs text-navy-500 ml-auto">共 {pagination?.total ?? 0} 个提案</span>
    </div>
  )

  const workbench = (
    <AdminWorkbench
      compact={embedded}
      listTitle="进化提案"
      toolbar={toolbar}
      listItems={items}
      selectedId={selectedId}
      onSelect={handleSelectProposal}
      getItemId={(item) => item.id}
      listLoading={loading}
      listEmpty={
        <div className="text-center space-y-3 max-w-sm">
          <p className="text-sm text-navy-300">还没有规则进化提案</p>
          <p className="text-xs text-navy-500 leading-relaxed">
            点击右上角「触发分析」，系统会扫描低分项目并自动生成修改提案
          </p>
        </div>
      }
      renderListItem={(item, { active, onSelect }) => (
        <button
          key={item.id}
          type="button"
          onClick={onSelect}
          className={cn(
            'w-full rounded-xl px-3 py-2.5 text-left border transition',
            active ? 'border-gold-500/35 bg-gold-400/10' : 'border-transparent hover:bg-white/[0.06]',
          )}
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-mono text-gold-400">#{item.id}</span>
            <ProposalStatusBadge status={item.status} />
          </div>
          <div className="text-sm font-medium text-white truncate mt-1">
            {item.target_skill || item.skill_name || '—'}
          </div>
          <div className="text-[10px] text-navy-400 truncate mt-0.5">
            {item.dimension || item.rule_type || '—'}
          </div>
          <div className="text-[10px] text-navy-500 mt-1">{formatDateTime(item.created_at)}</div>
        </button>
      )}
      listFooter={
        !embedded && pagination && pagination.total_pages > 1 ? (
          <div className="border-t border-white/5 p-2 flex items-center justify-between text-xs text-navy-500">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => patchParams({ page: page - 1 }, false)}
              className="disabled:opacity-40"
            >
              上一页
            </button>
            <span>
              第 {pagination.page} / {pagination.total_pages} 页
            </span>
            <button
              type="button"
              disabled={page >= pagination.total_pages}
              onClick={() => patchParams({ page: page + 1 }, false)}
              className="disabled:opacity-40"
            >
              下一页
            </button>
          </div>
        ) : null
      }
      detailLoading={detailLoading}
      detailEmpty="从左侧选择提案查看详情与审批"
    >
      {selectedProposal ? (
        <ProposalDetailView
          proposal={selectedProposal}
          onApprove={() => setApproveDialogOpen(true)}
          onReject={() => setRejectDialogOpen(true)}
          onApply={handleApply}
          actionLoading={actionLoading}
        />
      ) : null}
    </AdminWorkbench>
  )

  const dialogs = (
    <>
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
    </>
  )

  if (embedded) {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-white">规则进化提案</h3>
          <button
            type="button"
            onClick={() => setAnalyzeDialogOpen(true)}
            className="text-xs text-gold-400 hover:text-gold-300"
          >
            触发分析
          </button>
        </div>
        {workbench}
        {dialogs}
      </div>
    )
  }

  return (
    <AiConfigShell
      sectionId="evolution"
      actions={
        <button
          type="button"
          onClick={() => setAnalyzeDialogOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm hover:bg-gold-400/30"
        >
          <Zap className="w-4 h-4" />
          触发分析
        </button>
      }
    >
      <AdminMessage message={message} onClose={() => setMessage(null)} />
      {workbench}
      {dialogs}
    </AiConfigShell>
  )
}
