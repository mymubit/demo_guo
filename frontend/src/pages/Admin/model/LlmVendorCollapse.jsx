import { ChevronDown } from 'lucide-react'
import { useState } from 'react'

/**
 * 按 vendor 分组 catalog / preset / provider 列表。
 */
export function groupItemsByVendor(items, options = {}) {
  const getVendor = options.getVendor || ((item) => item.vendor || 'other')
  const getLabel =
    options.getVendorLabel ||
    ((item) => item.vendor_label || item.vendor || '其他')
  const getSort = options.getSortOrder || ((item) => item.sort_order ?? 0)

  const map = new Map()
  for (const item of items) {
    const key = getVendor(item) || 'other'
    const label = getLabel(item) || key
    if (!map.has(key)) {
      map.set(key, { vendor: key, label, items: [], minSort: getSort(item) })
    }
    const group = map.get(key)
    group.items.push(item)
    group.minSort = Math.min(group.minSort, getSort(item))
  }

  return [...map.values()].sort(
    (a, b) => a.minSort - b.minSort || a.label.localeCompare(b.label, 'zh-CN'),
  )
}

export function LlmVendorCollapse({
  label,
  count,
  hint,
  defaultOpen = false,
  children,
  className = '',
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <details
      className={`rounded-xl border border-white/10 bg-slate-900/40 group ${className}`}
      open={isOpen}
      onToggle={(event) => setIsOpen(event.currentTarget.open)}
    >
      <summary className="cursor-pointer list-none px-4 py-3 flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm text-white font-medium">{label}</p>
          {hint ? <p className="text-[10px] text-navy-400 mt-0.5">{hint}</p> : null}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-navy-400">{count} 个</span>
          <ChevronDown className="w-4 h-4 text-navy-400 transition group-open:rotate-180" />
        </div>
      </summary>
      <div className="px-3 pb-3 pt-1 space-y-2 border-t border-white/5">{children}</div>
    </details>
  )
}
