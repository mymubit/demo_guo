import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, AlertTriangle } from 'lucide-react'
import { Badge, Button, Card, EmptyState, MetricCard, Pagination } from '@/components/ui'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'
import { cardEnter, modalOverlay, modalPanel } from '@/constants/motion'
import { formatDateTime as formatDateTimeUtil } from '@/utils/date'

export function AdminPageHeader({ title, description, actions }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">{title}</h1>
        {description && <p className="text-navy-300 text-base leading-relaxed max-w-3xl">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 flex-wrap">{actions}</div>}
    </div>
  )
}

/** 后台通用 Tab 条（URL ?tab= 由页面自行同步） */
export function AdminTabBar({ tabs, active, onChange, className = '', stretch = false }) {
  if (!tabs?.length) return null
  return (
    <div
      className={cn(
        'flex flex-wrap gap-2.5 rounded-2xl border border-navy-600/25 bg-navy-900/55 p-1.5 shadow-card backdrop-blur-xl',
        stretch ? 'w-full' : 'w-fit',
        className,
      )}
    >
      {tabs.map((t) => {
        const Icon = t.icon
        const isActive = active === t.key
        return (
          <button
            key={t.key}
            type="button"
            onClick={() => onChange(t.key)}
            className={cn(
              'flex items-center gap-2.5 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all sf-focus-ring',
              stretch && 'flex-1 justify-center',
              isActive
                ? 'bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 shadow-lg shadow-gold-500/20'
                : 'text-navy-200 hover:bg-navy-800/55 hover:text-white',
            )}
          >
            {Icon ? <Icon className={ICON.lg} /> : null}
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
        'flex items-center justify-between gap-3 rounded-2xl border px-5 py-4',
        ok
          ? 'border-success-500/30 bg-success-500/10 text-success-300'
          : 'border-danger-500/30 bg-danger-500/10 text-danger-300',
      )}
    >
      <span className="text-sm">{message.text}</span>
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
    <Card padding="sm" className="flex flex-col gap-3 lg:flex-row lg:items-center">
      {children}
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
      className={cn('sf-control min-w-[220px] flex-1', className)}
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
    <Card padding="none" className={cn('overflow-hidden', mobileCardRender && 'md:bg-navy-900/55')}>
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
            <tr className="border-b border-navy-700/40 text-navy-400">
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
                className="border-b border-navy-800/60 hover:bg-navy-800/30 transition-colors"
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
            className="glass-card rounded-2xl p-6 max-w-md w-full shadow-modal"
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
