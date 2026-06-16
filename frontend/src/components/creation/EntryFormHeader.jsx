import { Check, ChevronRight } from 'lucide-react'

/**
 * 创意输入页 — 仅展示本入口的子步骤进度，避免与顶部三阶段指示器重复堆叠
 */
export default function EntryFormHeader({ entryMeta, currentStepIndex = 0 }) {
  const steps = entryMeta?.steps || []
  if (!steps.length) return null

  const maxActiveIndex = Math.max(0, steps.length - 2)

  return (
    <nav
      aria-label="填写进度"
      className="flex flex-wrap items-center gap-y-2 gap-x-1 py-3 px-4 rounded-xl border border-white/5 bg-slate-900/40"
    >
      {steps.map((step, idx) => {
        const isPipeline = idx === steps.length - 1
        const isPast = !isPipeline && idx < currentStepIndex
        const isCurrent = !isPipeline && idx === currentStepIndex && currentStepIndex <= maxActiveIndex
        const isFuture = isPipeline || idx > currentStepIndex

        return (
          <div key={step} className="flex items-center">
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs border transition-colors ${
                isCurrent
                  ? 'bg-gold-500/15 text-gold-300 border-gold-500/35 font-medium'
                  : isPast
                  ? 'bg-slate-800/50 text-navy-200 border-white/10'
                  : 'bg-slate-950/30 text-navy-400 border-white/5'
              }`}
            >
              <span
                className={`w-4 h-4 rounded-md text-[10px] font-bold flex items-center justify-center ${
                  isCurrent
                    ? 'bg-gold-500/25 text-gold-200'
                    : isPast
                    ? 'bg-gold-500/15 text-gold-400'
                    : 'border border-white/10 bg-white/[0.03] text-slate-400'
                }`}
              >
                {isPast ? <Check className="w-2.5 h-2.5" /> : idx + 1}
              </span>
              {step}
            </span>
            {idx < steps.length - 1 ? (
              <ChevronRight
                className={`w-3.5 h-3.5 mx-0.5 shrink-0 ${isFuture ? 'text-navy-700' : 'text-navy-500'}`}
              />
            ) : null}
          </div>
        )
      })}
    </nav>
  )
}
