import type { ReactNode } from 'react'
import { cn } from '@/utils/cn'

type Tone = 'action' | 'gold' | 'success' | 'warning' | 'danger' | 'info' | 'default'

const toneClass: Record<Tone, string> = {
  action: 'bg-action/10 text-action border-action/20',
  gold: 'bg-amber-50 text-amber-800 border-amber-100',
  success: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  warning: 'bg-amber-50 text-amber-700 border-amber-100',
  danger: 'bg-red-50 text-red-700 border-red-100',
  info: 'bg-sky-50 text-sky-700 border-sky-100',
  default: 'bg-slate-100 text-slate-700 border-slate-200',
}

export function Badge({
  tone = 'default',
  children,
  className,
}: {
  tone?: Tone
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium',
        toneClass[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}
