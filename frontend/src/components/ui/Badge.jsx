import { cn } from '@/utils/cn'

const tones = {
  brand: {
    bg: 'bg-brand-500/12',
    border: 'border-brand-500/30',
    text: 'text-brand-300',
  },
  accent: {
    bg: 'bg-accent-400/12',
    border: 'border-accent-400/30',
    text: 'text-accent-300',
  },
  success: {
    bg: 'bg-success-bg',
    border: 'border-success-border',
    text: 'text-success-light',
  },
  warning: {
    bg: 'bg-warning-bg',
    border: 'border-warning-border',
    text: 'text-warning-light',
  },
  danger: {
    bg: 'bg-danger-bg',
    border: 'border-danger-border',
    text: 'text-danger-light',
  },
  info: {
    bg: 'bg-info-bg',
    border: 'border-info-border',
    text: 'text-info-light',
  },
  default: {
    bg: 'bg-slate-800/55',
    border: 'border-white/10',
    text: 'text-slate-300',
  },
  // 旧名兼容
  gold: {
    bg: 'bg-accent-400/14',
    border: 'border-accent-400/30',
    text: 'text-accent-300',
  },
}

const sizes = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
}

export default function Badge({ tone = 'default', size = 'sm', icon, className, children }) {
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
