import { cn } from '@/utils/cn'

const tones = {
  brand: {
    bg: 'bg-gold-500/15',
    border: 'border-gold-500/30',
    text: 'text-gold-300',
  },
  accent: {
    bg: 'bg-gold-500/15',
    border: 'border-gold-500/30',
    text: 'text-gold-300',
  },
  success: {
    bg: 'bg-success/12',
    border: 'border-success/30',
    text: 'text-success-light',
  },
  warning: {
    bg: 'bg-warning/12',
    border: 'border-warning/30',
    text: 'text-warning-light',
  },
  danger: {
    bg: 'bg-danger/12',
    border: 'border-danger/30',
    text: 'text-danger-light',
  },
  info: {
    bg: 'bg-info/12',
    border: 'border-info/30',
    text: 'text-info-light',
  },
  default: {
    bg: 'bg-white/8',
    border: 'border-white/10',
    text: 'text-slate-300',
  },
  gold: {
    bg: 'bg-gold-500/15',
    border: 'border-gold-500/30',
    text: 'text-gold-300',
  },
}

const sizes = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
}

function Badge({ tone = 'default', size = 'sm', icon, className, children }) {
  const toneDef = tones[tone] || tones.default
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border font-medium leading-none',
        toneDef.bg,
        toneDef.border,
        toneDef.text,
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

export default Badge
export { Badge }
