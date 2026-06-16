import { useEffect, useMemo, useRef, useState } from 'react'
import { Search, X } from 'lucide-react'
import { cn } from '@/utils/cn'

function stepLabel(step) {
  return step.agent_name_zh || step.display_name || step.node_id
}

/** 键盘 / 打开步骤搜索面板 */
export default function OrchestrationStepSearch({
  steps = [],
  open,
  onOpenChange,
  onSelect,
  selectedNodeId,
}) {
  const [query, setQuery] = useState('')
  const inputRef = useRef(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    const ordered = [...steps].sort((a, b) => (a.chain_order || 0) - (b.chain_order || 0))
    if (!q) return ordered.slice(0, 12)
    return ordered.filter((step) => {
      const hay = [
        stepLabel(step),
        step.node_id,
        step.agent_id,
        step.agent_name,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return hay.includes(q)
    })
  }, [steps, query])

  useEffect(() => {
    function onKeyDown(event) {
      if ((event.key === '/' || (event.key === 'k' && (event.metaKey || event.ctrlKey))) && !event.target?.closest('input, textarea, select')) {
        event.preventDefault()
        onOpenChange?.(true)
      }
      if (event.key === 'Escape') onOpenChange?.(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onOpenChange])

  useEffect(() => {
    if (open) {
      setQuery('')
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => onOpenChange?.(true)}
        className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-300 hover:bg-white/[0.06]"
        title="搜索步骤 ( / )"
      >
        <Search className="w-3.5 h-3.5" />
        搜索步骤
        <kbd className="hidden rounded border border-white/10 px-1 text-[10px] text-navy-500 sm:inline">/</kbd>
      </button>
    )
  }

  return (
    <div className="fixed inset-0 z-[80] flex items-start justify-center pt-[12vh] px-4 bg-navy-950/70 backdrop-blur-sm">
      <div className="w-full max-w-lg overflow-hidden rounded-2xl border border-white/5 bg-slate-900/95 shadow-2xl">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
          <Search className="w-4 h-4 text-navy-400 shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="按名称、node_id、agent_id 搜索…"
            className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-navy-500"
          />
          <button
            type="button"
            onClick={() => onOpenChange?.(false)}
            className="rounded-lg p-1 text-navy-400 hover:bg-white/[0.06] hover:text-white"
            aria-label="关闭"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <ul className="max-h-[320px] overflow-y-auto py-1">
          {filtered.length === 0 ? (
            <li className="px-4 py-6 text-sm text-navy-400 text-center">无匹配步骤</li>
          ) : (
            filtered.map((step) => {
              const active = step.node_id === selectedNodeId
              return (
                <li key={step.id || step.node_id}>
                  <button
                    type="button"
                    onClick={() => {
                      onSelect?.(step)
                      onOpenChange?.(false)
                    }}
                    className={cn(
                      'w-full text-left px-4 py-2.5 flex items-center gap-3 hover:bg-white/[0.06]',
                      active && 'bg-gold-500/10',
                    )}
                  >
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-white/[0.05] text-[11px] font-bold text-navy-300 flex items-center justify-center shrink-0">
                      {step.chain_order}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm text-white truncate">{stepLabel(step)}</div>
                      <div className="text-xs font-mono text-navy-300 truncate">{step.node_id}</div>
                    </div>
                  </button>
                </li>
              )
            })
          )}
        </ul>
      </div>
    </div>
  )
}
