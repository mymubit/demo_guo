import Card from './Card'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'

const tones = {
  default: 'text-navy-300 bg-navy-800/60 border-navy-700/40',
  gold: 'text-gold-300 bg-gold-400/12 border-gold-400/25',
  success: 'text-success-300 bg-success-500/12 border-success-500/25',
  warning: 'text-warning-300 bg-warning-500/12 border-warning-500/25',
  danger: 'text-danger-300 bg-danger-500/12 border-danger-500/25',
  info: 'text-info-300 bg-info-500/12 border-info-500/25',
}

export default function MetricCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = 'default',
  className,
}) {
  return (
    <Card className={cn('min-w-0', className)} padding="lg">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-sm text-navy-400">{label}</div>
          <div className="mt-2 truncate text-3xl font-bold tracking-tight text-white">{value}</div>
          {hint ? <div className="mt-2 text-xs leading-relaxed text-navy-400">{hint}</div> : null}
        </div>
        {Icon ? (
          <div className={cn('flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border', tones[tone] || tones.default)}>
            <Icon className={ICON.lg} />
          </div>
        ) : null}
      </div>
    </Card>
  )
}
