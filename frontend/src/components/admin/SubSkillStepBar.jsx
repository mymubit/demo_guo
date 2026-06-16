import StepStatusMark from '@/components/ui/StepStatusMark'
import {
  executionStatusLabel,
  subSkillTypeLabel,
} from '@/utils/agentExecutionLabels'

const STATUS_STYLES = {
  executed: {
    dot: 'bg-green-400 ring-green-400/30',
    line: 'bg-green-500/40',
    text: 'text-green-300',
    bg: 'bg-green-500/10 border-green-500/25',
  },
  failed: {
    dot: 'bg-red-400 ring-red-400/30',
    line: 'bg-red-500/40',
    text: 'text-red-300',
    bg: 'bg-red-500/10 border-red-500/25',
  },
  skipped: {
    dot: 'bg-slate-500 ring-slate-500/30',
    line: 'bg-white/10',
    text: 'text-navy-400',
    bg: 'bg-white/[0.04] border-white/10',
  },
  pending: {
    dot: 'bg-slate-700 ring-white/10 border border-dashed border-white/20',
    line: 'bg-white/[0.05]',
    text: 'text-navy-400',
    bg: 'bg-slate-900/40 border-white/5 border-dashed',
  },
  running: {
    dot: 'bg-amber-400 ring-amber-400/30 animate-pulse',
    line: 'bg-amber-500/30',
    text: 'text-amber-300',
    bg: 'bg-amber-500/10 border-amber-500/25',
  },
}

export function SubSkillLegend({ className = '' }) {
  const items = [
    { status: 'executed', label: '已执行' },
    { status: 'failed', label: '失败' },
    { status: 'skipped', label: '已跳过' },
    { status: 'pending', label: '未跑到' },
  ]
  return (
    <div className={`flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-navy-400 ${className}`}>
      {items.map((item) => {
        const style = STATUS_STYLES[item.status]
        return (
          <span key={item.status} className="inline-flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${style.dot}`} />
            {item.label}
          </span>
        )
      })}
    </div>
  )
}

export default function SubSkillStepBar({ steps = [], compact = false, showLegend = false, activeIndex = -1 }) {
  if (!steps.length) {
    return <p className="text-xs text-navy-400">暂无子技能记录</p>
  }

  return (
    <div className="space-y-2">
      {showLegend ? <SubSkillLegend /> : null}
      <div className={`flex flex-wrap gap-2 ${compact ? '' : 'gap-y-3'}`}>
        {steps.map((step, index) => {
          const style = STATUS_STYLES[step.status] || STATUS_STYLES.pending
          const typeLabel = subSkillTypeLabel(step.type)
          const statusLabel = executionStatusLabel(step.status)
          return (
            <div
              key={step.id || index}
              title={[step.id, typeLabel, statusLabel, step.message].filter(Boolean).join(' · ')}
              className={`relative min-w-[120px] max-w-[220px] flex-1 rounded-xl border px-3 py-2 ${style.bg} ${
                index === activeIndex ? 'ring-2 ring-gold-400/45 border-gold-500/35' : ''
              }`}
            >
              {!compact && index < steps.length - 1 ? (
                <span
                  className={`hidden sm:block absolute top-1/2 -right-2 w-2 h-px ${style.line}`}
                  aria-hidden
                />
              ) : null}
              <div className="flex items-start gap-2">
                <span className={`mt-1 w-2 h-2 rounded-full shrink-0 ${style.dot}`} />
                <div className="min-w-0 flex-1">
                  <p className={`text-xs font-medium leading-snug ${style.text}`}>
                    {step.label || step.id}
                  </p>
                  <p className="text-[10px] text-navy-400 mt-0.5 truncate">
                    {typeLabel}
                    {step.cli ? ` · ${step.cli}` : ''}
                  </p>
                  <p className="text-[10px] text-navy-400 mt-0.5 flex items-center gap-1">
                    {statusLabel}
                    {step.status === 'failed' || step.status === 'skipped' ? (
                      <StepStatusMark status={step.status} className="w-3 h-3" />
                    ) : null}
                  </p>
                  {!compact && step.message ? (
                    <p className="text-[10px] text-red-300/80 mt-1 line-clamp-2">{step.message}</p>
                  ) : null}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
