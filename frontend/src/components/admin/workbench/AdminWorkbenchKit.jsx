import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Loader2, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/utils/cn'
import { AdminTabBar, AdminLoading } from '@/components/admin/AdminUI'
import { modalOverlay, modalPanel } from '@/constants/motion'

/** 左列表 + 右详情工作台壳层 */
export function AdminWorkbench({
  toolbar,
  listHeader,
  listFooter,
  listEmpty,
  listLoading,
  listItems = [],
  selectedId,
  onSelect,
  getItemId = (item) => item.id,
  renderListItem,
  detailHeader,
  detailTabs,
  activeTab,
  onTabChange,
  detailLoading,
  detailEmpty = '请从左侧选择一项',
  children,
  className,
}) {
  return (
    <div className={cn('space-y-4', className)}>
      {toolbar ? <div className="sf-console-panel p-4">{toolbar}</div> : null}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_minmax(0,1fr)] lg:min-h-[560px]">
        <div className="sf-console-panel flex flex-col overflow-hidden">
          {listHeader}
          <div className="flex-1 overflow-y-auto p-2 space-y-1 max-h-[calc(100vh-320px)]">
            {listLoading ? (
              <div className="py-12 text-center text-sm text-navy-400">
                <Loader2 className="mx-auto mb-2 h-5 w-5 animate-spin" />
                加载中…
              </div>
            ) : listItems.length === 0 ? (
              listEmpty || <p className="px-3 py-8 text-sm text-navy-400 text-center">暂无数据</p>
            ) : (
              listItems.map((item) => {
                const id = getItemId(item)
                const active = id === selectedId
                if (renderListItem) return renderListItem(item, { id, active, onSelect: () => onSelect(id) })
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => onSelect(id)}
                    className={cn(
                      'w-full rounded-xl px-3 py-2.5 text-left text-sm transition border',
                      active
                        ? 'border-gold-500/35 bg-gold-400/10 text-gold-200'
                        : 'border-transparent text-navy-200 hover:bg-white/[0.06]',
                    )}
                  >
                    {item.name || String(id)}
                  </button>
                )
              })
            )}
          </div>
          {listFooter}
        </div>

        <div className="sf-console-panel flex flex-col overflow-hidden min-h-[420px]">
          {detailHeader}
          {detailTabs?.length ? (
            <div className="px-4 pt-3 border-b border-white/5">
              <AdminTabBar tabs={detailTabs} active={activeTab} onChange={onTabChange} stretch />
            </div>
          ) : null}
          <div className="flex-1 overflow-y-auto p-4 lg:max-h-[calc(100vh-280px)]">
            {detailLoading ? (
              <AdminLoading label="加载详情…" />
            ) : selectedId == null && !children ? (
              <div className="flex h-full min-h-[240px] items-center justify-center text-sm text-navy-400">
                {detailEmpty}
              </div>
            ) : (
              children
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

/** 详情顶栏：标题 + 徽章 + 操作 */
export function AdminDetailHeader({ title, subtitle, badges, meta, actions, className }) {
  return (
    <div className={cn('flex flex-wrap items-start justify-between gap-3 px-4 py-3 border-b border-white/5', className)}>
      <div className="min-w-0 flex-1">
        <h2 className="text-lg font-semibold text-white truncate">{title}</h2>
        {subtitle ? <p className="mt-0.5 text-xs font-mono text-navy-400 truncate">{subtitle}</p> : null}
        {meta ? <p className="mt-1 text-sm text-navy-300">{meta}</p> : null}
        {badges?.length ? <div className="mt-2 flex flex-wrap gap-2">{badges}</div> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div> : null}
    </div>
  )
}

const LIFECYCLE_TONE = {
  draft: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  active: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  gray: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  deprecated: 'bg-red-500/15 text-red-300 border-red-500/30',
}

const LIFECYCLE_LABEL = {
  draft: '草稿',
  active: '上线',
  gray: '灰度',
  deprecated: '废弃',
}

export function AdminLifecycleBadge({ status, grayWeight }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border', LIFECYCLE_TONE[status] || LIFECYCLE_TONE.draft)}>
      {LIFECYCLE_LABEL[status] || status}
      {status === 'gray' && grayWeight != null && grayWeight < 100 ? (
        <span className="ml-1 opacity-80">{grayWeight}%</span>
      ) : null}
    </span>
  )
}

export function AdminHealthBadges({ health }) {
  if (!health) return null
  const items = [
    ['Prompt', health.prompt_ok],
    ['Route', health.route_ok],
    ['Contract', health.contract_ok],
  ]
  return (
    <div className="flex flex-wrap gap-2">
      {items.map(([label, ok]) => (
        <span
          key={label}
          className={cn(
            'rounded-full px-2 py-0.5 text-[11px]',
            ok ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/15 text-red-300',
          )}
        >
          {label}: {ok ? 'OK' : '缺失'}
        </span>
      ))}
    </div>
  )
}

export function AdminPenetrationLink({ to, label, className }) {
  if (!to) return null
  return (
    <Link
      to={to}
      className={cn(
        'inline-flex items-center gap-1 text-xs text-gold-300 hover:text-gold-200 transition',
        className,
      )}
    >
      {label}
      <ArrowRight className="h-3 w-3" />
    </Link>
  )
}

/** 文本摘要预览 */
export function AdminTextPreview({ text, maxLines = 4, className }) {
  const value = String(text || '').trim()
  if (!value) return <p className="text-sm text-navy-500 italic">（空）</p>
  const lines = value.split('\n').slice(0, maxLines)
  return (
    <pre className={cn('text-sm text-navy-200 whitespace-pre-wrap font-mono leading-relaxed', className)}>
      {lines.join('\n')}
      {value.split('\n').length > maxLines ? '\n…' : ''}
    </pre>
  )
}

/** JSON / Markdown 全屏 Drawer 编辑 */
export function AdminJsonDrawer({ open, title, value, onChange, onClose, onSave, saving, language = 'json' }) {
  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => { if (e.key === 'Escape') onClose?.() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open ? (
        <motion.div {...modalOverlay} className="fixed inset-0 z-50 flex items-stretch justify-end bg-black/60">
          <motion.div
            {...modalPanel}
            className="w-full max-w-3xl h-full sf-console-panel flex flex-col shadow-modal border-l border-white/10"
          >
            <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-white/10">
              <h3 className="text-base font-semibold text-white">{title}</h3>
              <div className="flex items-center gap-2">
                {onSave ? (
                  <button
                    type="button"
                    disabled={saving}
                    onClick={onSave}
                    className="px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm hover:bg-gold-400/30 disabled:opacity-50"
                  >
                    {saving ? '保存中…' : '保存'}
                  </button>
                ) : null}
                <button type="button" onClick={onClose} className="p-2 rounded-lg text-navy-400 hover:text-white hover:bg-white/5">
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
            <textarea
              value={value}
              onChange={(e) => onChange?.(e.target.value)}
              spellCheck={false}
              className="flex-1 w-full resize-none bg-transparent p-5 font-mono text-sm text-navy-100 focus:outline-none"
              placeholder={language === 'json' ? '{}' : ''}
            />
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}

/** 行级 diff（Prompt / 规则） */
export function AdminDiffView({ leftLabel, rightLabel, leftText = '', rightText = '', className }) {
  const leftLines = String(leftText || '').split('\n')
  const rightLines = String(rightText || '').split('\n')
  const max = Math.max(leftLines.length, rightLines.length)
  const rows = []
  for (let i = 0; i < max; i += 1) {
    const l = leftLines[i] ?? ''
    const r = rightLines[i] ?? ''
    rows.push({ type: l === r ? 'same' : 'diff', left: l, right: r })
  }
  return (
    <div className={cn('rounded-xl border border-white/10 overflow-hidden text-xs font-mono', className)}>
      <div className="grid grid-cols-2 border-b border-white/10 bg-black/30 text-navy-300">
        <div className="px-3 py-2">{leftLabel}</div>
        <div className="px-3 py-2 border-l border-white/10">{rightLabel}</div>
      </div>
      <div className="max-h-64 overflow-y-auto">
        {rows.map((row, idx) => (
          <div
            key={idx}
            className={cn(
              'grid grid-cols-2 border-b border-white/5',
              row.type === 'diff' ? 'bg-amber-500/5' : '',
            )}
          >
            <div className={cn('px-3 py-1 whitespace-pre-wrap', row.type === 'diff' ? 'text-red-300/90' : 'text-navy-300')}>
              {row.left || ' '}
            </div>
            <div className={cn('px-3 py-1 border-l border-white/5 whitespace-pre-wrap', row.type === 'diff' ? 'text-emerald-300/90' : 'text-navy-300')}>
              {row.right || ' '}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/** 键值对只读摘要 */
export function AdminKvGrid({ rows = [] }) {
  return (
    <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
      {rows.map(({ label, value }) => (
        <div key={label}>
          <dt className="text-xs text-navy-400 mb-0.5">{label}</dt>
          <dd className="text-navy-100 break-words">{value ?? '—'}</dd>
        </div>
      ))}
    </dl>
  )
}

/** 深色表单字段 */
export function AdminField({ label, children, className }) {
  return (
    <label className={cn('block', className)}>
      {label ? <span className="sf-label text-xs mb-1 block">{label}</span> : null}
      {children}
    </label>
  )
}

export function adminBtnPrimary(className) {
  return cn(
    'inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm hover:bg-gold-400/30 disabled:opacity-50 transition',
    className,
  )
}

export function adminBtnSecondary(className) {
  return cn(
    'inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 bg-white/[0.03] text-sm text-navy-200 hover:bg-white/[0.06] disabled:opacity-50 transition',
    className,
  )
}

export function adminBtnDanger(className) {
  return cn(
    'inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border border-red-500/30 text-red-300 text-xs hover:bg-red-500/10 transition',
    className,
  )
}
