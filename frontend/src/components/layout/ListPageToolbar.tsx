import type { ReactNode } from 'react'
import { Search } from 'lucide-react'
import { cn } from '@/utils/cn'

export type ToolbarFilter = {
  id: string
  label: string
  value: string
  options: Array<{ value: string; label: string }>
  onChange: (value: string) => void
}

interface ListPageToolbarProps {
  search?: string
  onSearchChange?: (value: string) => void
  searchPlaceholder?: string
  filters?: ToolbarFilter[]
  count?: number
  countLabel?: string
  actions?: ReactNode
  className?: string
}

/** 列表页统一工具栏：搜索 + 筛选 + 计数 + 操作区。 */
export function ListPageToolbar({
  search,
  onSearchChange,
  searchPlaceholder = '搜索…',
  filters = [],
  count,
  countLabel = '条',
  actions,
  className,
}: ListPageToolbarProps) {
  const showSearch = onSearchChange != null

  return (
    <div
      className={cn(
        'sf-panel flex flex-wrap items-center justify-between gap-3 px-4 py-3',
        className,
      )}
    >
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-3">
        {showSearch ? (
          <label className="relative min-w-[12rem] flex-1 sm:max-w-xs">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
            <input
              type="search"
              className="sf-control w-full py-1.5 pl-9"
              placeholder={searchPlaceholder}
              value={search ?? ''}
              onChange={(e) => onSearchChange(e.target.value)}
            />
          </label>
        ) : null}
        {filters.map((filter) => (
          <label key={filter.id} className="flex items-center gap-2 text-sm text-ink-muted">
            {filter.label}
            <select
              className="sf-control w-auto py-1.5"
              value={filter.value}
              onChange={(e) => filter.onChange(e.target.value)}
            >
              {filter.options.map((opt) => (
                <option key={opt.value || '__all__'} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      <div className="flex shrink-0 flex-wrap items-center gap-2">
        {count != null ? (
          <span className="text-xs text-ink-faint">
            共 {count} {countLabel}
          </span>
        ) : null}
        {actions}
      </div>
    </div>
  )
}
