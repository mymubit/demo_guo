import type { ReactNode } from 'react'
import { cn } from '@/utils/cn'

export function Tabs({
  items,
  value,
  onChange,
  className,
}: {
  items: Array<{ id: string; label: string; disabled?: boolean }>
  value: string
  onChange: (id: string) => void
  className?: string
}) {
  return (
    <div className={cn('flex flex-wrap gap-1 border-b border-slate-200', className)} role="tablist">
      {items.map((item) => {
        const active = item.id === value
        return (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={active}
            disabled={item.disabled}
            onClick={() => onChange(item.id)}
            className={cn(
              'relative px-3 py-2 text-sm font-medium transition',
              active ? 'text-brand-600' : 'text-ink-muted hover:text-ink',
              item.disabled && 'cursor-not-allowed opacity-40',
            )}
          >
            {item.label}
            {active ? (
              <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand-500" />
            ) : null}
          </button>
        )
      })}
    </div>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      {description ? <p className="mt-2 max-w-md text-sm text-ink-muted">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      aria-live="assertive"
      className="flex items-start justify-between gap-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <p className="whitespace-pre-wrap">{message}</p>
      {onRetry ? (
        <button type="button" className="shrink-0 font-medium underline" onClick={onRetry}>
          重试
        </button>
      ) : null}
    </div>
  )
}

export function LoadingBlock({ label = '加载中…' }: { label?: string }) {
  return (
    <div
      className="flex items-center justify-center gap-3 py-16 text-sm text-ink-muted"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <span
        className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-r-transparent"
        aria-hidden="true"
      />
      {label}
    </div>
  )
}
