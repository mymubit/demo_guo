import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, AlertTriangle, ChevronDown, Info } from 'lucide-react'
import { Badge, Button, Card, EmptyState, MetricCard, Pagination } from '@/components/ui'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'
import { renderLucideIcon } from '@/utils/renderLucideIcon'
import { cardEnter, modalOverlay, modalPanel } from '@/constants/motion'
import { formatDateTime as formatDateTimeUtil } from '@/utils/date'
import {
  AdminPageHeader as AdminDesignPageHeader,
  AdminPanel,
  AdminDataTable,
  ToolbarSearch,
  KpiTile,
  Sparkline,
  AdminPillTabs,
  AdminDonutChart,
} from './AdminPrimitives'

export {
  AdminDesignPageHeader,
  AdminPanel,
  AdminDataTable,
  ToolbarSearch,
  KpiTile,
  Sparkline,
  AdminPillTabs,
  AdminDonutChart,
}

export function AdminPageHeader({ title, description, subtitle, crumbs, toolbar, actions }) {
  if (crumbs || subtitle || toolbar) {
    return (
      <AdminDesignPageHeader
        crumbs={crumbs}
        title={title}
        subtitle={subtitle}
        description={description}
        toolbar={toolbar}
        actions={actions}
      />
    )
  }
  return (
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">{title}</h1>
        {description && (
          <p className="text-navy-400 text-sm leading-relaxed max-w-3xl mt-1.5">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 flex-wrap">{actions}</div>}
    </div>
  )
}

/** 可折叠说明条 — 减少页头与正文重复提示 */
export function AdminContextBanner({ summary, children, defaultOpen = false }) {
  return (
    <details className="sf-console-panel-subtle group" open={defaultOpen || undefined}>
      <summary className="cursor-pointer list-none px-4 py-3 flex items-center justify-between gap-3 sf-focus-ring rounded-2xl">
        <span className="inline-flex items-center gap-2 text-sm text-navy-300">
          <Info className={cn(ICON.sm, 'text-gold-400/80 shrink-0')} />
          {summary}
        </span>
        <ChevronDown className={cn(ICON.sm, 'text-navy-400 transition-transform group-open:rotate-180')} />
      </summary>
      <div className="px-4 pb-4 text-sm text-navy-400 leading-relaxed border-t border-white/5 -mt-1 pt-3">
        {children}
      </div>
    </details>
  )
}

/** Tab 区 + 单行提示 */
export function AdminTabSection({ hint, children, className }) {
  return (
    <div className={cn('space-y-3', className)}>
      {children}
      {hint ? (
        <p className="text-xs text-navy-400 leading-relaxed border-l-2 border-gold-500/25 pl-3">{hint}</p>
      ) : null}
    </div>
  )
}

/** 配置面板内分区 */
export function AdminInspectorSection({ title, children, className }) {
  return (
    <section className={cn('sf-console-panel-subtle p-4 space-y-3', className)}>
      {title ? <h4 className="text-sm font-medium text-navy-100">{title}</h4> : null}
      {children}
    </section>
  )
}

/** 后台通用 Tab 条（URL ?tab= 由页面自行同步） */
export function AdminTabBar({ tabs, active, onChange, className = '', stretch = false }) {
  if (!tabs?.length) return null
  return (
    <div
      className={cn(
        'flex flex-wrap gap-2.5 sf-console-panel p-1.5 shadow-card',
        stretch ? 'w-full' : 'w-fit',
        className,
      )}
    >
      {tabs.map((t) => {
        const isActive = active === t.key
        return (
          <button
            key={t.key}
            type="button"
            onClick={() => onChange(t.key)}
            className={cn(
              'flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all sf-focus-ring border',
              stretch && 'flex-1 justify-center',
              isActive
                ? 'border-gold-500/35 bg-gold-400/10 text-gold-200 shadow-sm'
                : 'text-navy-300 border-transparent hover:bg-white/[0.06] hover:text-white',
            )}
          >
            {renderLucideIcon(t.icon, ICON.md)}
            {t.label}
          </button>
        )
      })}
    </div>
  )
}

export function AdminMessage({ message, onClose }) {
  if (!message) return null
  const ok = message.type !== 'error'
  return (
    <motion.div
      {...cardEnter}
      className={cn(
        'flex items-center justify-between gap-3 rounded-xl border px-4 py-3',
        ok
          ? 'border-success-500/30 bg-success-500/10 text-success-300'
          : 'border-danger-500/40 bg-danger-500/15 text-danger-200',
      )}
    >
      <span className="inline-flex items-center gap-2 text-sm font-medium">
        {!ok ? <AlertTriangle className={cn(ICON.sm, 'shrink-0')} /> : null}
        {message.text}
      </span>
      {onClose && (
        <button type="button" onClick={onClose} className="text-xs opacity-70 hover:opacity-100 sf-focus-ring">
          关闭
        </button>
      )}
    </motion.div>
  )
}

export function AdminLoading({ label = '加载中…' }) {
  return (
    <div className="flex items-center justify-center py-20 text-navy-300 gap-3">
      <Loader2 className={cn(ICON.lg, 'animate-spin text-gold-400')} />
      <span>{label}</span>
    </div>
  )
}

export function AdminEmpty({ title = '暂无数据', description }) {
  return <EmptyState title={title} description={description} compact className="rounded-2xl py-12" />
}

export function AdminStatGrid({ items, columns }) {
  const count = items?.length ?? 0
  const colClass =
    columns === 4 || count === 4
      ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
      : columns === 3 || count === 3
        ? 'grid-cols-1 sm:grid-cols-3'
        : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5'

  return (
    <div className={cn('grid gap-5', colClass)}>
      {items.map((item) => (
        <MetricCard
          key={item.label}
          label={item.label}
          value={item.value}
          hint={item.hint}
          icon={item.icon}
          tone={item.tone}
        />
      ))}
    </div>
  )
}

export function AdminToolbar({ children }) {
  return (
    <Card padding="sm">
      <div className="sf-toolbar">{children}</div>
    </Card>
  )
}

export function AdminSearchInput({ value, onChange, placeholder, className = '' }) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={cn('sf-control h-11 min-w-0', className)}
    />
  )
}

export function AdminTable({ columns, rows, rowKey = 'id', emptyText = '暂无数据', mobileCardRender }) {
  if (!rows?.length) {
    return <AdminEmpty title={emptyText} />
  }
  const getRowKey = (row, index) =>
    typeof rowKey === 'function' ? rowKey(row, index) : row[rowKey] || row.user_id || row.order_no || index

  return (
    <Card padding="none" className={cn('overflow-hidden', mobileCardRender && 'md:bg-slate-900/55')}>
      {mobileCardRender ? (
        <div className="space-y-3 p-3 md:hidden">
          {rows.map((row, index) => (
            <div key={getRowKey(row, index)}>{mobileCardRender(row, index)}</div>
          ))}
        </div>
      ) : null}
      <div className={cn('overflow-x-auto overscroll-x-contain', mobileCardRender && 'hidden md:block')}>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/5 text-navy-400">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn('px-5 py-4 text-left font-medium whitespace-nowrap', col.className)}
                >
                  {col.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={getRowKey(row)}
                className="border-b border-white/5 hover:bg-white/[0.03] transition-colors"
              >
                {columns.map((col) => (
                  <td key={col.key} className={cn('px-5 py-4 align-middle', col.className)}>
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

export function AdminPagination({ page, totalPages, total, onPageChange }) {
  return <Pagination page={page} totalPages={totalPages} total={total} onPageChange={onPageChange} />
}

export function AdminConfirmDialog({ open, title, message, confirmText = '确认', loading, onConfirm, onCancel }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          {...modalOverlay}
          className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-navy-950/80 backdrop-blur-sm"
        >
          <motion.div
            {...modalPanel}
            className="sf-console-panel p-6 max-w-md w-full shadow-modal"
          >
            <div className="flex items-start gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gold-500/15 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className={`${ICON.lg} text-gold-400`} />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <p className="text-sm text-navy-300 mt-2 leading-relaxed">{message}</p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={onCancel}>
                取消
              </Button>
              <Button variant="gold" isLoading={loading} onClick={onConfirm}>
                {loading ? '处理中…' : confirmText}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export function AdminBadge({ children, tone = 'default' }) {
  return <Badge tone={tone}>{children}</Badge>
}

export function formatDateTime(value) {
  return formatDateTimeUtil(value)
}
