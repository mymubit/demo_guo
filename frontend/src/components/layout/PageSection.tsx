import type { ReactNode } from 'react'
import { cn } from '@/utils/cn'

interface PageSectionProps {
  eyebrow?: string
  title: string
  description?: ReactNode
  actions?: ReactNode
  children?: ReactNode
  className?: string
}

/** 页面内区块标题与间距统一。 */
export function PageSection({
  eyebrow,
  title,
  description,
  actions,
  children,
  className,
}: PageSectionProps) {
  return (
    <section className={cn('mb-8 last:mb-0', className)}>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          {eyebrow ? (
            <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
              {eyebrow}
            </div>
          ) : null}
          <h2
            className={cn(
              'font-semibold tracking-tight text-ink',
              eyebrow ? 'mt-2 text-lg' : 'text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-faint',
            )}
          >
            {title}
          </h2>
          {description ? (
            <div className="mt-1.5 text-sm text-ink-muted">{description}</div>
          ) : null}
        </div>
        {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
      {children}
    </section>
  )
}
