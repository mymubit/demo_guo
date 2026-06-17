/**
 * 系统配置中心
 *
 * 包含 4 个 Tab：
 * 1. 全局开关：创作功能总开关、题材/流水线/Provider 启停
 * 2. 阈值配置：评分线、失败率告警、节点超时
 * 3. 配额规则：默认节点币价、会员免费额度
 * 4. 敏感词：列表+批量导入
 */
import { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  Coins,
  FileWarning,
  Plus,
  Power,
  RefreshCcw,
  Save,
  Scale,
  Settings2,
  ShieldAlert,
  Timer,
  Upload,
} from 'lucide-react'

import AdminShell from '@/components/admin/AdminShell'
import {
  AdminBadge,
  AdminPageHeader,
  AdminPanel,
  AdminPillTabs,
} from '@/components/admin/AdminUI'
import { Button } from '@/components/ui'
import { adminSystemConfig } from '@/services/api'
import { ICON } from '@/constants/iconSizes'
import { cn } from '@/utils/cn'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const TABS = [
  { key: 'switch', label: '全局开关', icon: Power },
  { key: 'threshold', label: '阈值配置', icon: Timer },
  { key: 'quota', label: '配额规则', icon: Scale },
  { key: 'sensitive', label: '敏感词', icon: FileWarning },
]

const SENSITIVITY = [
  { value: 'high', label: '高' },
  { value: 'medium', label: '中' },
  { value: 'low', label: '低' },
]

function Toggle({ checked, onChange, disabled, label, hint }) {
  return (
    <label
      className={cn(
        'flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-slate-900/40 p-4 transition-colors',
        disabled ? 'opacity-60' : 'hover:bg-slate-900/60',
      )}
    >
      <div className="min-w-0">
        <div className="text-sm font-medium text-white">{label}</div>
        {hint ? <div className="mt-1 text-xs text-navy-400">{hint}</div> : null}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors',
          checked ? 'bg-gold-500' : 'bg-slate-600',
        )}
      >
        <span
          className={cn(
            'inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform',
            checked ? 'translate-x-5' : 'translate-x-0.5',
          )}
        />
      </button>
    </label>
  )
}

function NumberField({ label, unit, value, onChange, min, max, hint, disabled }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-4">
      <div className="flex items-baseline justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-white">{label}</div>
          {hint ? <div className="mt-1 text-xs text-navy-400">{hint}</div> : null}
        </div>
        <div className="text-[11px] uppercase tracking-wider text-navy-400">{unit}</div>
      </div>
      <input
        type="number"
        value={value ?? ''}
        min={min}
        max={max}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
        className="mt-3 w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-lg font-semibold text-white focus:border-gold-500 focus:outline-none"
      />
      {(min !== undefined || max !== undefined) && (
        <div className="mt-2 text-[11px] text-navy-400">
          {min !== undefined ? `最小 ${min}` : ''} {max !== undefined ? `· 最大 ${max}` : ''}
        </div>
      )}
    </div>
  )
}

function FlashMessage({ tone = 'info', text, onClose }) {
  const tones = {
    info: 'border-info-500/30 bg-info-500/10 text-info-200',
    success: 'border-success-500/30 bg-success-500/10 text-success-200',
    error: 'border-danger-500/30 bg-danger-500/10 text-danger-200',
  }
  const icon = tone === 'success' ? CheckCircle2 : AlertCircle
  return (
    <div className={cn('flex items-center justify-between gap-3 rounded-2xl border p-3 text-sm', tones[tone])}>
      <div className="inline-flex items-center gap-2">
        {renderLucideIcon(icon, ICON.md)}
        {text}
      </div>
      {onClose ? (
        <button type="button" onClick={onClose} className="text-xs opacity-70 hover:opacity-100">关闭</button>
      ) : null}
    </div>
  )
}

function SwitchPanel({ onMessage }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await adminSystemConfig.getGlobalSwitches()
      setItems((res && res.items) || [])
    } catch (err) {
      onMessage?.({ tone: 'error', text: err?.message || '加载全局开关失败' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleToggle = (key, next) => {
    setItems((prev) => prev.map((it) => (it.config_key === key ? { ...it, enabled: next } : it)))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await adminSystemConfig.updateGlobalSwitches({
        items: items.map((it) => ({ config_key: it.config_key, enabled: !!it.enabled })),
        change_reason: '后台开关批量更新',
      })
      onMessage?.({ tone: 'success', text: `已更新 ${res?.updated ?? 0} 个开关` })
    } catch (err) {
      onMessage?.({ tone: 'error', text: err?.message || '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  const labelMap = {
    'creation.enabled': { label: '创作功能总开关', hint: '关闭后 C 端用户无法创建项目' },
    'creation.theme_enabled': { label: '题材模板', hint: '关闭后禁止使用剧本主题模板' },
    'creation.pipeline_enabled': { label: '流水线', hint: '关闭后只能走单体节点' },
    'llm.provider.openai': { label: 'Provider · OpenAI', hint: 'OpenAI 模型路由启停' },
    'llm.provider.volcano': { label: 'Provider · 火山引擎', hint: '火山引擎模型路由启停' },
    'llm.provider.deepseek': { label: 'Provider · DeepSeek', hint: 'DeepSeek 模型路由启停' },
  }

  return (
    <AdminPanel
      title="全局开关"
      sub="总开关 / 题材 / 流水线 / Provider 启停"
      action={
        <Button
          variant="ghost"
          size="sm"
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-2"
        >
          <RefreshCcw className={cn(ICON.sm, loading && 'animate-spin')} />
          刷新
        </Button>
      }
    >
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {items.map((item) => {
          const meta = labelMap[item.config_key] || { label: item.config_key, hint: '' }
          return (
            <Toggle
              key={item.config_key}
              label={meta.label}
              hint={meta.hint}
              checked={!!item.enabled}
              onChange={(v) => handleToggle(item.config_key, v)}
              disabled={loading || saving}
            />
          )
        })}
      </div>

      <div className="mt-4 flex justify-end">
        <Button onClick={handleSave} disabled={saving || loading} className="inline-flex items-center gap-2">
          <Save className={ICON.sm} />
          {saving ? '保存中…' : '保存修改'}
        </Button>
      </div>
    </AdminPanel>
  )
}

function ThresholdPanel({ onMessage }) {
  const [items, setItems] = useState({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await adminSystemConfig.getThresholds()
      setItems(res || {})
    } catch (err) {
      onMessage?.({ tone: 'error', text: err?.message || '加载阈值配置失败' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleChange = (key, val) => {
    setItems((prev) => ({ ...prev, [key]: { ...(prev[key] || {}), value: val } }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updates = {}
      Object.keys(items).forEach((k) => {
        updates[k] = items[k]?.value
      })
      const res = await adminSystemConfig.updateThresholds({
        items: updates,
        change_reason: '后台阈值调整',
      })
      onMessage?.({ tone: 'success', text: `已更新 ${res?.updated ?? 0} 项阈值` })
    } catch (err) {
      onMessage?.({ tone: 'error', text: err?.message || '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  const specs = [
    { key: 'creation.quality.pass_threshold', icon: ShieldAlert, accent: 'text-warning-300' },
    { key: 'monitoring.failure_alert_threshold', icon: AlertCircle, accent: 'text-danger-300' },
    { key: 'creation.node_timeout_default', icon: Timer, accent: 'text-info-300' },
    { key: 'creation.retry_max_attempts_default', icon: RefreshCcw, accent: 'text-gold-300' },
  ]

  return (
    <AdminPanel
      title="阈值配置"
      sub="评分通过线 / 失败率告警 / 节点超时 / 默认重试"
      action={
        <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="inline-flex items-center gap-2">
          <RefreshCcw className={cn(ICON.sm, loading && 'animate-spin')} />
          刷新
        </Button>
      }
    >
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {specs.map(({ key, icon, accent }) => {
          const item = items[key] || {}
          return (
            <NumberField
              key={key}
              label={
                <span className="inline-flex items-center gap-2">
                  {renderLucideIcon(icon, cn(ICON.md, accent))}
                  {item.name || key}
                </span>
              }
              unit={item.unit || ''}
              value={item.value}
              min={item.min}
              max={item.max}
              disabled={loading || saving}
              onChange={(v) => handleChange(key, v)}
            />
          )
        })}
      </div>
      <div className="mt-4 flex justify-end">
        <Button onClick={handleSave} disabled={saving || loading} className="inline-flex items-center gap-2">
          <Save className={ICON.sm} />
          {saving ? '保存中…' : '保存阈值'}
        </Button>
      </div>
    </AdminPanel>
  )
}

function QuotaPanel({ onMessage }) {
  const [items, setItems] = useState({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await adminSystemConfig.getQuotaRules()
      setItems(res || {})
    } catch (err) {
      onMessage?.({ tone: 'error', text: err?.message || '加载配额规则失败' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleChange = (key, val) => {
    setItems((prev) => ({ ...prev, [key]: { ...(prev[key] || {}), value: val } }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updates = {}
      Object.keys(items).forEach((k) => {
        updates[k] = items[k]?.value
      })
      const res = await adminSystemConfig.updateQuotaRules({
        items: updates,
        change_reason: '后台配额调整',
      })
      onMessage?.({ tone: 'success', text: `已更新 ${res?.updated ?? 0} 项配额` })
    } catch (err) {
      onMessage?.({ tone: 'error', text: err?.message || '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  const specs = [
    { key: 'billing.default_node_coin_cost', icon: Coins, accent: 'text-warning-300' },
    { key: 'membership.free_quota_monthly', icon: Scale, accent: 'text-gold-300' },
    { key: 'membership.vip_extra_quota', icon: Settings2, accent: 'text-info-300' },
  ]

  return (
    <AdminPanel
      title="配额规则"
      sub="默认节点币价 / 会员免费额度 / VIP 额外配额"
      action={
        <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="inline-flex items-center gap-2">
          <RefreshCcw className={cn(ICON.sm, loading && 'animate-spin')} />
          刷新
        </Button>
      }
    >
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {specs.map(({ key, icon, accent }) => {
          const item = items[key] || {}
          return (
            <NumberField
              key={key}
              label={
                <span className="inline-flex items-center gap-2">
                  {renderLucideIcon(icon, cn(ICON.md, accent))}
                  {item.name || key}
                </span>
              }
              unit={item.unit || ''}
              value={item.value}
              min={item.min}
              max={item.max}
              disabled={loading || saving}
              onChange={(v) => handleChange(key, v)}
            />
          )
        })}
      </div>
      <div className="mt-4 flex justify-end">
        <Button onClick={handleSave} disabled={saving || loading} className="inline-flex items-center gap-2">
          <Save className={ICON.sm} />
          {saving ? '保存中…' : '保存配额'}
        </Button>
      </div>
    </AdminPanel>
  )
}

function SensitivePanel({ onMessage }) {
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState({ total: 0, page: 1, page_size: 20 })
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [severity, setSeverity] = useState('')
  const [page, setPage] = useState(1)
  const [bulkText, setBulkText] = useState('')
  const [bulkSeverity, setBulkSeverity] = useState('medium')
  const [bulkCategory, setBulkCategory] = useState('')
  const [bulkNote, setBulkNote] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const res = await adminSystemConfig.listSensitiveWords({
        page,
        page_size: 20,
        keyword,
        severity,
      })
      setItems(res?.items || [])
      setPagination(res?.pagination || { total: 0, page: 1, page_size: 20 })
    } catch (err) {
      onMessage?.({ tone: 'error', text: err?.message || '加载敏感词失败' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  const handleImport = async () => {
    const words = bulkText
      .split(/[\n,，]/)
      .map((s) => s.trim())
      .filter(Boolean)
    if (!words.length) {
      onMessage?.({ tone: 'error', text: '请输入至少一个敏感词' })
      return
    }
    setImporting(true)
    try {
      const res = await adminSystemConfig.importSensitiveWords({
        words,
        severity: bulkSeverity,
        category: bulkCategory,
        note: bulkNote,
      })
      onMessage?.({
        tone: 'success',
        text: `新增 ${res?.created ?? 0} 条，跳过 ${res?.skipped ?? 0} 条已存在`,
      })
      setBulkText('')
      setBulkNote('')
      setPage(1)
      load()
    } catch (err) {
      onMessage?.({ tone: 'error', text: err?.message || '导入失败' })
    } finally {
      setImporting(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil((pagination.total || 0) / (pagination.page_size || 20)))

  return (
    <div className="space-y-4">
      <AdminPanel
        title="批量导入"
        sub="每行一个敏感词；已存在的词会被自动跳过"
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          <label className="block lg:col-span-3">
            <span className="mb-1 block text-xs text-navy-400">敏感词（每行一个，或用逗号分隔）</span>
            <textarea
              rows={5}
              value={bulkText}
              onChange={(e) => setBulkText(e.target.value)}
              placeholder={'暴力\n涉政\n赌博'}
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 font-mono text-sm text-white focus:border-gold-500 focus:outline-none"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs text-navy-400">严重程度</span>
            <select
              value={bulkSeverity}
              onChange={(e) => setBulkSeverity(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white focus:border-gold-500 focus:outline-none"
            >
              {SENSITIVITY.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="mb-1 block text-xs text-navy-400">分类</span>
            <input
              value={bulkCategory}
              onChange={(e) => setBulkCategory(e.target.value)}
              placeholder="例如：涉政/广告/暴恐"
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white focus:border-gold-500 focus:outline-none"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs text-navy-400">备注</span>
            <input
              value={bulkNote}
              onChange={(e) => setBulkNote(e.target.value)}
              placeholder="批次说明（可选）"
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white focus:border-gold-500 focus:outline-none"
            />
          </label>
        </div>
        <div className="mt-3 flex justify-end">
          <Button
            onClick={handleImport}
            disabled={importing}
            className="inline-flex items-center gap-2"
          >
            <Upload className={ICON.sm} />
            {importing ? '导入中…' : '导入敏感词'}
          </Button>
        </div>
      </AdminPanel>

      <AdminPanel
        title="敏感词列表"
        sub="append-only 表，由人工 SQL 软删"
        action={
          <Button
            variant="ghost"
            size="sm"
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-2"
          >
            <RefreshCcw className={cn(ICON.sm, loading && 'animate-spin')} />
            刷新
          </Button>
        }
      >
        <div className="mb-3 sf-toolbar">
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                setPage(1)
                load()
              }
            }}
            placeholder="搜索敏感词/备注"
            className="flex-1 rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white focus:border-gold-500 focus:outline-none"
          />
          <select
            value={severity}
            onChange={(e) => {
              setSeverity(e.target.value)
              setPage(1)
            }}
            className="rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white focus:border-gold-500 focus:outline-none"
          >
            <option value="">全部等级</option>
            {SENSITIVITY.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <Button variant="ghost" size="sm" onClick={() => { setPage(1); load() }}>
            搜索
          </Button>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/5">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="bg-slate-900/60 text-[11px] uppercase tracking-wider text-navy-400">
                <th className="px-3 py-2 text-left">敏感词</th>
                <th className="px-3 py-2 text-left">分类</th>
                <th className="px-3 py-2 text-left">严重程度</th>
                <th className="px-3 py-2 text-left">备注</th>
                <th className="px-3 py-2 text-left">创建人</th>
                <th className="px-3 py-2 text-left">创建时间</th>
              </tr>
            </thead>
            <tbody>
              {!items.length ? (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-navy-400">
                    {loading ? '加载中…' : '暂无敏感词'}
                  </td>
                </tr>
              ) : (
                items.map((row) => (
                  <tr key={row.id} className="border-t border-white/5">
                    <td className="px-3 py-2 font-mono text-slate-100">{row.word}</td>
                    <td className="px-3 py-2 text-slate-300">{row.category || '—'}</td>
                    <td className="px-3 py-2">
                      <AdminBadge tone={
                        row.severity === 'high' ? 'danger'
                          : row.severity === 'medium' ? 'warning' : 'default'
                      }>
                        {row.severity_display || row.severity}
                      </AdminBadge>
                    </td>
                    <td className="px-3 py-2 text-slate-300">{row.note || '—'}</td>
                    <td className="px-3 py-2 text-slate-300">{row.created_by || '—'}</td>
                    <td className="px-3 py-2 text-slate-300">
                      {row.created_at ? new Date(row.created_at).toLocaleString('zh-CN', { hour12: false }) : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex items-center justify-between text-xs text-navy-400">
          <div>共 {pagination.total || 0} 条</div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              上一页
            </Button>
            <span>{page} / {totalPages}</span>
            <Button
              variant="ghost"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              下一页
            </Button>
          </div>
        </div>
      </AdminPanel>
    </div>
  )
}

export default function AdminSystemConfig() {
  const [activeTab, setActiveTab] = useState('switch')
  const [flash, setFlash] = useState(null)

  const handleMessage = (msg) => {
    setFlash({ ...msg, id: Date.now() })
    if (msg?.tone !== 'error') {
      window.setTimeout(() => setFlash((cur) => (cur && cur.id === msg.id ? null : cur)), 4000)
    }
  }

  const tabContent = useMemo(() => {
    switch (activeTab) {
      case 'threshold':
        return <ThresholdPanel onMessage={handleMessage} />
      case 'quota':
        return <QuotaPanel onMessage={handleMessage} />
      case 'sensitive':
        return <SensitivePanel onMessage={handleMessage} />
      case 'switch':
      default:
        return <SwitchPanel onMessage={handleMessage} />
    }
  }, [activeTab])

  return (
    <AdminShell>
      <div className="space-y-6">
        <AdminPageHeader
          title="系统配置中心"
          description="全局开关 / 阈值 / 配额 / 敏感词；变更即时生效并写入审计日志"
        />

        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <AdminPillTabs tabs={TABS} active={activeTab} onChange={setActiveTab} />
          <div className="text-[11px] text-navy-400">
            <Plus className={cn(ICON.sm, 'inline-block align-[-2px]')} /> 修改将调用 PUT API 持久化
          </div>
        </div>

        {flash ? (
          <FlashMessage tone={flash.tone} text={flash.text} onClose={() => setFlash(null)} />
        ) : null}

        {tabContent}
      </div>
    </AdminShell>
  )
}
