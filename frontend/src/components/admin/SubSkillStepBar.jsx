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
    dot: 'bg-navy-500 ring-navy-500/30',
    line: 'bg-navy-600/40',
    text: 'text-navy-400',
    bg: 'bg-navy-800/40 border-navy-600/30',
  },
  pending: {
    dot: 'bg-navy-700 ring-navy-600/30 border border-dashed border-navy-500',
    line: 'bg-navy-700/30',
    text: 'text-navy-500',
    bg: 'bg-navy-900/30 border-navy-700/25 border-dashed',
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

export default function SubSkillStepBar({ steps = [], compact = false, showLegend = false }) {
  if (!steps.length) {
    return <p className="text-xs text-navy-500">暂无子技能记录</p>
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
              className={`relative min-w-[120px] max-w-[220px] flex-1 rounded-xl border px-3 py-2 ${style.bg}`}
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
                  <p className="text-[10px] text-navy-500 mt-0.5 truncate">
                    {typeLabel}
                    {step.cli ? ` · ${step.cli}` : ''}
                  </p>
                  <p className="text-[10px] text-navy-500 mt-0.5 flex items-center gap-1">
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
