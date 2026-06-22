import { cn } from '@/utils/cn'

const tones = {
  brand: {
    bg: 'bg-brand-50',
    border: 'border-brand-200',
    text: 'text-brand-700',
  },
  accent: {
    bg: 'bg-accent-50',
    border: 'border-accent-200',
    text: 'text-accent-700',
  },
  success: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    text: 'text-green-700',
  },
  warning: {
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-700',
  },
  danger: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-700',
  },
  info: {
    bg: 'bg-cyan-50',
    border: 'border-cyan-200',
    text: 'text-cyan-700',
  },
  default: {
    bg: 'bg-gray-100',
    border: 'border-gray-200',
    text: 'text-gray-600',
  },
  // 旧名兼容
  gold: {
    bg: 'bg-accent-50',
    border: 'border-accent-200',
    text: 'text-accent-700',
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
