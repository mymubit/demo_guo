import Card from './Card'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const tones = {
  default: 'text-gray-500 bg-gray-100 border-gray-200',
  gold: 'text-accent-700 bg-accent-50 border-accent-200',
  success: 'text-green-700 bg-green-50 border-green-200',
  warning: 'text-amber-700 bg-amber-50 border-amber-200',
  danger: 'text-red-700 bg-red-50 border-red-200',
  info: 'text-cyan-700 bg-cyan-50 border-cyan-200',
}

export default function MetricCard({
  label,
  value,
  hint,
  icon,
  tone = 'default',
  className,
}) {
  return (
    <Card className={cn('min-w-0', className)} padding="lg">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-sm text-gray-500">{label}</div>
          <div className="mt-2 truncate text-3xl font-bold tracking-tight text-gray-900">{value}</div>
          {hint ? <div className="mt-2 text-xs leading-relaxed text-gray-400">{hint}</div> : null}
        </div>
        {icon ? (
          <div className={cn('flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border', tones[tone] || tones.default)}>
            {renderLucideIcon(icon, ICON.lg)}
          </div>
        ) : null}
      </div>
    </Card>
  )
}
