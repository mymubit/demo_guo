import { NODE_RUN_STATES } from '@/utils/orchestrationNodeStates'
import { cn } from '@/utils/cn'

export default function OrchestrationNodeStateBadge({ state = 'idle', compact = false, className }) {
  const meta = NODE_RUN_STATES[state] || NODE_RUN_STATES.idle
  if (compact) {
    return (
      <span
        className={cn('inline-block w-2 h-2 rounded-full shrink-0', meta.dot, className)}
        title={meta.label}
        aria-label={meta.label}
      />
    )
  }
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] border',
        meta.badge,
        className,
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full', meta.dot)} />
      {meta.label}
    </span>
  )
}
