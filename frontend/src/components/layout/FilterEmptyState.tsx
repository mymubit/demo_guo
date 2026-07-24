import type { ReactNode } from 'react'
import { FilterX, Inbox } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'

interface FilterEmptyStateProps {
  title: string
  description?: string
  onClearFilters?: () => void
  action?: ReactNode
  variant?: 'default' | 'filter' | 'inbox'
  className?: string
}

/** 空态：无数据 / 筛选无结果 / 占位引导。 */
export function FilterEmptyState({
  title,
  description,
  onClearFilters,
  action,
  variant = 'default',
  className,
}: FilterEmptyStateProps) {
  const Icon = variant === 'filter' ? FilterX : Inbox

  return (
    <div
      className={cn(
        'sf-panel flex min-h-[20rem] flex-col items-center justify-center px-6 py-16 text-center',
        className,
      )}
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-canvas-muted text-ink-faint">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      {description ? <p className="mt-2 max-w-md text-sm text-ink-muted">{description}</p> : null}
      {onClearFilters ? (
        <div className="mt-5">
          <Button size="sm" variant="secondary" onClick={onClearFilters}>
            清除筛选
          </Button>
        </div>
      ) : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}
