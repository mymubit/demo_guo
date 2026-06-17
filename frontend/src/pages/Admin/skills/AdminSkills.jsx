import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  Edit3,
  Rocket,
  RotateCcw,
  Trash2,
  RefreshCw,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react'
import { adminSkill } from '@/services/admin/skill'
import AdminShell from '@/components/admin/AdminShell'
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

const TIER_OPTIONS = [
  { key: '', label: '全部层级' },
  { key: 'foundation', label: 'Foundation' },
  { key: 'business', label: 'Business' },
  { key: 'tool', label: 'Tool' },
]

const STATUS_OPTIONS = [
  { key: '', label: '全部状态' },
  { key: 'draft', label: '草稿' },
  { key: 'active', label: '已发布' },
  { key: 'gray', label: '灰度' },
  { key: 'deprecated', label: '已废弃' },
]

const STATUS_TONE = {
  draft: 'default',
  active: 'success',
  gray: 'warning',
  deprecated: 'danger',
  archived: 'danger',
}

const STATUS_LABEL = {
  draft: '草稿',
  active: '已发布',
  gray: '灰度',
  deprecated: '已废弃',
  archived: '已归档',
}

function SkillStatusBadge({ status }) {
  return (
    <AdminBadge tone={STATUS_TONE[status] || 'default'}>
      {STATUS_LABEL[status] || status}
    </AdminBadge>
  )
}

/** 技能列表页 */
function SkillListPage({ onSelect }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState(null)
  const [publishDialog, setPublishDialog] = useState(null)
  const [rollbackDialog, setRollbackDialog] = useState(null)
  const [deprecateDialog, setDeprecateDialog] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const keyword = searchParams.get('q') || ''
  const tier = searchParams.get('tier') || ''
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
      const res = await adminSkill.listDefinitions({
        page,
        page_size: 20,
        keyword: keyword.trim() || undefined,
        tier: tier || undefined,
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
  }, [page, keyword, tier, status])

  useEffect(() => {
    load()
  }, [load])

  async function handlePublish() {
    if (!publishDialog) return
    setActionLoading(true)
    try {
      await adminSkill.publishDefinition(publishDialog.skill.id, {
        gray_weight: publishDialog.grayWeight,
      })
      setMessage({ type: 'success', text: '技能已发布' })
      setPublishDialog(null)
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '发布失败' })
    } finally {
      setActionLoading(false)
    }
  }

  async function handleRollback() {
    if (!rollbackDialog) return
    setActionLoading(true)
    try {
      await adminSkill.rollbackDefinition(rollbackDialog.skill.id)
      setMessage({ type: 'success', text: '技能已回滚到上一版本' })
      setRollbackDialog(null)
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '回滚失败' })
    } finally {
      setActionLoading(false)
    }
  }

  async function handleDeprecate() {
    if (!deprecateDialog) return
    setActionLoading(true)
    try {
      await adminSkill.deprecateDefinition(deprecateDialog.skill.id)
      setMessage({ type: 'success', text: '技能已废弃' })
      setDeprecateDialog(null)
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '废弃失败' })
    } finally {
      setActionLoading(false)
    }
  }

  const columns = [
    {
      key: 'id',
      title: '技能ID',
      render: (row) => (
        <button
          type="button"
          onClick={() => onSelect(row)}
          className="text-gold-400 hover:text-gold-300 font-mono text-xs hover:underline"
        >
          {row.id}
        </button>
      ),
    },
    {
      key: 'name',
      title: '名称',
      render: (row) => (
        <div>
          <div className="text-white font-medium">{row.name}</div>
          {row.description ? (
            <div className="text-xs text-navy-400 line-clamp-1 mt-0.5">{row.description}</div>
          ) : null}
        </div>
      ),
    },
    {
      key: 'tier',
      title: '层级',
      render: (row) => (
        <span className="text-xs text-navy-200 capitalize">{row.tier || '—'}</span>
      ),
    },
    {
      key: 'sub_category',
      title: '子分类',
      render: (row) => (
        <span className="text-xs text-navy-300">{row.sub_category || '—'}</span>
      ),
    },
    {
      key: 'version',
      title: '版本',
      render: (row) => (
        <span className="text-xs text-navy-300 font-mono">v{row.version || 1}</span>
      ),
    },
    {
      key: 'status',
      title: '状态',
      render: (row) => <SkillStatusBadge status={row.status} />,
    },
    {
      key: 'quota',
      title: '配额',
      render: (row) => (
        <span className="text-xs text-navy-300">
          {row.quota_limit != null ? `${row.quota_limit}/日` : '—'}
        </span>
      ),
    },
    {
      key: 'published_by',
      title: '发布人',
      render: (row) => (
        <span className="text-xs text-navy-300">{row.published_by || '—'}</span>
      ),
    },
    {
      key: 'last_invoked_at',
      title: '最近调用',
      render: (row) => (
        <span className="text-xs text-navy-400 whitespace-nowrap">
          {row.last_invoked_at ? formatDateTime(row.last_invoked_at) : '—'}
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
            <Edit3 className="w-3.5 h-3.5" />
            编辑
          </button>
          {row.status === 'draft' && (
            <button
              type="button"
              onClick={() =>
                setPublishDialog({ skill: row, grayWeight: 0 })
              }
              className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300"
            >
              <Rocket className="w-3.5 h-3.5" />
              发布
            </button>
          )}
          {(row.status === 'active' || row.status === 'gray') && (
            <button
              type="button"
              onClick={() =>
                setPublishDialog({
                  skill: row,
                  grayWeight: row.gray_weight || 50,
                })
              }
              className="inline-flex items-center gap-1 text-xs text-yellow-400 hover:text-yellow-300"
            >
              <Rocket className="w-3.5 h-3.5" />
              灰度
            </button>
          )}
          {(row.status === 'active' || row.status === 'gray') && (
            <button
              type="button"
              onClick={() => setRollbackDialog({ skill: row })}
              className="inline-flex items-center gap-1 text-xs text-orange-400 hover:text-orange-300"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              回滚
            </button>
          )}
          {row.status !== 'deprecated' && (
            <button
              type="button"
              onClick={() => setDeprecateDialog({ skill: row })}
              className="inline-flex items-center gap-1 text-xs text-red-400 hover:text-red-300"
            >
              <Trash2 className="w-3.5 h-3.5" />
              废弃
            </button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminToolbar>
        <AdminSearchInput
          value={keyword}
          onChange={(v) => patchParams({ q: v })}
          placeholder="搜索技能 ID / 名称…"
        />
        <select
          value={tier}
          onChange={(e) => patchParams({ tier: e.target.value })}
          className="sf-control"
        >
          {TIER_OPTIONS.map((o) => (
            <option key={o.key} value={o.key}>
              {o.label}
            </option>
          ))}
        </select>
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
        <AdminLoading label="加载技能…" />
      ) : (
        <AdminPanel
          title="技能定义"
          sub={`共 ${pagination?.total ?? 0} 个技能`}
        >
          <AdminTable
            rowKey="id"
            rows={items}
            columns={columns}
            emptyText="暂无技能"
          />
          <AdminPagination
            page={pagination?.page || 1}
            totalPages={pagination?.total_pages || 1}
            total={pagination?.total}
            onPageChange={(p) => patchParams({ page: p }, false)}
          />
        </AdminPanel>
      )}

      {/* 发布弹窗 */}
      <AnimatePresence>
        {publishDialog && (
          <PublishDialog
            skill={publishDialog.skill}
            grayWeight={publishDialog.grayWeight}
            onGrayWeightChange={(v) =>
              setPublishDialog((prev) => ({ ...prev, grayWeight: v }))
            }
            loading={actionLoading}
            onConfirm={handlePublish}
            onCancel={() => setPublishDialog(null)}
          />
        )}
      </AnimatePresence>

      {/* 回滚弹窗 */}
      <AdminConfirmDialog
        open={!!rollbackDialog}
        title="回滚技能"
        message={`确认回滚「${rollbackDialog?.skill?.name}」到上一版本？`}
        confirmText="确认回滚"
        loading={actionLoading}
        onConfirm={handleRollback}
        onCancel={() => setRollbackDialog(null)}
      />

      {/* 废弃弹窗 */}
      <AdminConfirmDialog
        open={!!deprecateDialog}
        title="废弃技能"
        message={`确认废弃「${deprecateDialog?.skill?.name}」？废弃后将不再可用。`}
        confirmText="确认废弃"
        loading={actionLoading}
        onConfirm={handleDeprecate}
        onCancel={() => setDeprecateDialog(null)}
      />
    </div>
  )
}

/** 发布弹窗 */
function PublishDialog({ skill, grayWeight, onGrayWeightChange, loading, onConfirm, onCancel }) {
  return (
    <motion.div
      {...modalOverlay}
      className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-navy-950/80 backdrop-blur-sm"
    >
      <motion.div
        {...modalPanel}
        className="sf-console-panel p-6 max-w-md w-full shadow-modal"
      >
        <div className="flex items-start gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/15 flex items-center justify-center flex-shrink-0">
            <Rocket className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">发布技能</h3>
            <p className="text-sm text-navy-300 mt-1">
              {skill.name}
              <span className="text-navy-500 font-mono ml-2">v{skill.version}</span>
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-navy-300 mb-2">
              灰度权重：{grayWeight}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={grayWeight}
              onChange={(e) => onGrayWeightChange(Number(e.target.value))}
              className="sf-control w-full"
            />
            <div className="flex justify-between text-xs text-navy-500 mt-1">
              <span>0%（全量）</span>
              <span>50%（均衡）</span>
              <span>100%（灰度）</span>
            </div>
          </div>

          {grayWeight === 0 && (
            <div className="flex items-start gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3">
              <AlertTriangle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-emerald-300">
                技能将直接全量发布，所有用户均可使用。
              </p>
            </div>
          )}

          {grayWeight > 0 && (
            <div className="flex items-start gap-2 rounded-lg border border-yellow-500/20 bg-yellow-500/10 p-3">
              <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-yellow-300">
                灰度发布后，按 user_id hash 命中的用户将使用新版本，其余继续使用当前版本。
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 mt-6">
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
            onClick={onConfirm}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-300 text-sm hover:bg-emerald-500/30 disabled:opacity-50"
          >
            {loading ? '发布中…' : grayWeight === 0 ? '全量发布' : '灰度发布'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

/** 技能详情页 */
function SkillDetailPage({ skill, onBack, onMessage }) {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [detail, setDetail] = useState(null)
  const [stats, setStats] = useState(null)
  const [versions, setVersions] = useState([])
  const [form, setForm] = useState({})

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [detailRes, statsRes, versionsRes] = await Promise.all([
        adminSkill.getDefinition(skill.id),
        adminSkill.getDefinitionStats(skill.id).catch(() => null),
        adminSkill.listDefinitionVersions(skill.id).catch(() => []),
      ])
      setDetail(detailRes)
      setStats(statsRes)
      setVersions(Array.isArray(versionsRes) ? versionsRes : [])
      setForm({
        name: detailRes.name,
        tier: detailRes.tier,
        sub_category: detailRes.sub_category,
        system_hint: detailRes.system_hint || '',
        description: detailRes.description || '',
        timeout_seconds: detailRes.timeout_seconds || 30,
        retry_count: detailRes.retry_count || 0,
        fallback_enabled: detailRes.fallback_enabled || false,
        quota_limit: detailRes.quota_limit || null,
      })
    } catch (e) {
      onMessage({ type: 'error', text: e.message || '加载详情失败' })
    } finally {
      setLoading(false)
    }
  }, [skill.id, onMessage])

  useEffect(() => {
    load()
  }, [load])

  async function handleSave() {
    setSaving(true)
    try {
      await adminSkill.updateDefinition(skill.id, form)
      onMessage({ type: 'success', text: '保存成功' })
      load()
    } catch (e) {
      onMessage({ type: 'error', text: e.message || '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <AdminLoading label="加载技能详情…" />
  }

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
        <span className="text-sm text-gold-400 font-mono">{skill.id}</span>
        <SkillStatusBadge status={detail?.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 左侧：基础信息 */}
        <AdminPanel title="基础信息">
          <div className="space-y-4">
            <label className="block">
              <span className="text-xs text-navy-400 mb-1 block">名称</span>
              <input
                type="text"
                value={form.name || ''}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className="sf-control"
              />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-xs text-navy-400 mb-1 block">层级</span>
                <select
                  value={form.tier || ''}
                  onChange={(e) => setForm((f) => ({ ...f, tier: e.target.value }))}
                  className="sf-control"
                >
                  <option value="">未设置</option>
                  <option value="foundation">Foundation</option>
                  <option value="business">Business</option>
                  <option value="tool">Tool</option>
                </select>
              </label>
              <label className="block">
                <span className="text-xs text-navy-400 mb-1 block">子分类</span>
                <input
                  type="text"
                  value={form.sub_category || ''}
                  onChange={(e) => setForm((f) => ({ ...f, sub_category: e.target.value }))}
                  className="sf-control"
                  placeholder="如：scene_gen"
                />
              </label>
            </div>

            <label className="block">
              <span className="text-xs text-navy-400 mb-1 block">描述</span>
              <input
                type="text"
                value={form.description || ''}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                className="sf-control"
              />
            </label>

            <label className="block">
              <span className="text-xs text-navy-400 mb-1 block">
                System Hint
                <span className="text-navy-500 ml-1">支持 {{变量}} 占位符</span>
              </span>
              <textarea
                rows={6}
                value={form.system_hint || ''}
                onChange={(e) => setForm((f) => ({ ...f, system_hint: e.target.value }))}
                className="sf-control font-mono text-xs"
                spellCheck={false}
              />
            </label>

            <button
              type="button"
              disabled={saving}
              onClick={handleSave}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm hover:bg-gold-400/30 disabled:opacity-50"
            >
              <Edit3 className="w-4 h-4" />
              {saving ? '保存中…' : '保存修改'}
            </button>
          </div>
        </AdminPanel>

        {/* 右侧：执行策略 + 统计 */}
        <div className="space-y-4">
          <AdminPanel title="执行策略">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <label className="block">
                  <span className="text-xs text-navy-400 mb-1 block">超时（秒）</span>
                  <input
                    type="number"
                    min="1"
                    value={form.timeout_seconds || 30}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, timeout_seconds: Number(e.target.value) }))
                    }
                    className="sf-control"
                  />
                </label>
                <label className="block">
                  <span className="text-xs text-navy-400 mb-1 block">重试次数</span>
                  <input
                    type="number"
                    min="0"
                    value={form.retry_count || 0}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, retry_count: Number(e.target.value) }))
                    }
                    className="sf-control"
                  />
                </label>
              </div>

              <label className="inline-flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.fallback_enabled || false}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, fallback_enabled: e.target.checked }))
                  }
                  className="rounded border-white/20"
                />
                <span className="text-sm text-navy-200">启用降级策略</span>
              </label>

              <label className="block">
                <span className="text-xs text-navy-400 mb-1 block">日配额</span>
                <input
                  type="number"
                  min="0"
                  value={form.quota_limit ?? ''}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      quota_limit: e.target.value ? Number(e.target.value) : null,
                    }))
                  }
                  className="sf-control"
                  placeholder="0 = 不限制"
                />
              </label>
            </div>
          </AdminPanel>

          <AdminPanel title="版本信息">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-navy-400">当前版本</span>
                <span className="text-white font-mono">v{detail?.version || 1}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-navy-400">灰度权重</span>
                <span className="text-white">{detail?.gray_weight ?? 0}%</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-navy-400">发布人</span>
                <span className="text-navy-200">{detail?.published_by || '—'}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-navy-400">发布时间</span>
                <span className="text-navy-300">
                  {detail?.published_at ? formatDateTime(detail.published_at) : '—'}
                </span>
              </div>
            </div>
          </AdminPanel>

          {/* 调用统计 */}
          {stats ? (
            <AdminPanel title="调用统计">
              <div className="grid grid-cols-2 gap-3">
                <StatCard label="今日调用" value={stats.today_calls ?? 0} />
                <StatCard label="本周调用" value={stats.week_calls ?? 0} />
                <StatCard label="本月调用" value={stats.month_calls ?? 0} />
                <StatCard label="总调用量" value={stats.total_calls ?? 0} />
                <StatCard label="成功率" value={stats.success_rate != null ? `${stats.success_rate}%` : '—'} />
                <StatCard label="平均耗时" value={stats.avg_duration != null ? `${stats.avg_duration}ms` : '—'} />
              </div>
            </AdminPanel>
          ) : null}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
      <div className="text-xs text-navy-400">{label}</div>
      <div className="text-lg font-bold text-white mt-1">{value}</div>
    </div>
  )
}

/** 主组件 */
export default function AdminSkills() {
  const [searchParams] = useSearchParams()
  const [message, setMessage] = useState(null)
  const [selectedSkill, setSelectedSkill] = useState(null)

  const isDetail = selectedSkill != null

  const crumbs = isDetail
    ? [{ label: 'Console' }, { label: '技能管理' }, { label: '技能详情' }]
    : [{ label: 'Console' }, { label: '技能管理' }]

  return (
    <AdminShell hideDescription>
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminPageHeader
        crumbs={crumbs}
        title="技能管理"
        subtitle="Agent 技能定义 / 版本管理 / 调用统计"
        actions={
          !isDetail ? (
            <button
              type="button"
              onClick={() => setSelectedSkill({ id: '__new__', name: '新建技能', status: 'draft' })}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm hover:bg-gold-400/30"
            >
              <Plus className="w-4 h-4" />
              新增技能
            </button>
          ) : null
        }
      />

      {isDetail ? (
        <SkillDetailPage
          skill={selectedSkill}
          onBack={() => setSelectedSkill(null)}
          onMessage={setMessage}
        />
      ) : (
        <SkillListPage onSelect={setSelectedSkill} />
      )}
    </AdminShell>
  )
}
