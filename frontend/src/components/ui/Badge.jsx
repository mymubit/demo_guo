import { cn } from '@/utils/cn'

const tones = {
  default: 'border-navy-700/45 bg-navy-800/55 text-navy-200',
  gold: 'border-gold-400/30 bg-gold-400/14 text-gold-300',
  success: 'border-success-500/30 bg-success-500/12 text-success-300',
  warning: 'border-warning-500/30 bg-warning-500/12 text-warning-300',
  danger: 'border-danger-500/30 bg-danger-500/12 text-danger-300',
  info: 'border-info-500/30 bg-info-500/12 text-info-300',
}

const sizes = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
}

export default function Badge({ tone = 'default', size = 'sm', icon, className, children }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border font-medium leading-none',
        tones[tone] || tones.default,
        sizes[size] || sizes.sm,
        className,
      )}
    >
      {icon}
      {children}
    </span>
  )
}

export function StatusBadge({ status, children, className }) {
  const tone =
    status === 'success' || status === 'completed' || status === 'active'
      ? 'success'
      : status === 'warning' || status === 'running' || status === 'pending'
        ? 'warning'
        : status === 'danger' || status === 'failed' || status === 'inactive'
          ? 'danger'
          : 'default'

  return (
    <Badge tone={tone} className={className}>
      {children}
    </Badge>
  )
}
