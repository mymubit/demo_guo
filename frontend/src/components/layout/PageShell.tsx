import type { ReactNode } from 'react'
import { cn } from '@/utils/cn'

type PageWidth = 'fluid' | 'form' | 'narrow'

const widthClass: Record<PageWidth, string> = {
  /** 列表 / 运维 / 日志：吃满可用宽度 */
  fluid: 'max-w-[min(100%,90rem)]',
  /** 设置与表单：稍宽但仍可读 */
  form: 'max-w-5xl',
  /** 极简表单（登录类除外） */
  narrow: 'max-w-3xl',
}

interface PageShellProps {
  title: string
  description?: ReactNode
  actions?: ReactNode
  children: ReactNode
  width?: PageWidth
  className?: string
}

/** 统一页面骨架：页头 + 可配置版心，避免各页窄柱各自为政。 */
export function PageShell({
  title,
  description,
  actions,
  children,
  width = 'fluid',
  className,
}: PageShellProps) {
  return (
    <div className={cn('mx-auto w-full px-4 py-5 sm:px-6 sm:py-6 lg:px-8', widthClass[width], className)}>
      <header className="mb-5 flex flex-wrap items-start justify-between gap-4 border-b border-border pb-4">
        <div className={cn('min-w-0', width === 'fluid' ? 'max-w-4xl' : 'max-w-3xl')}>
          <h1 className="text-lg font-semibold text-ink">{title}</h1>
          {description ? (
            <div className="mt-1.5 text-sm leading-relaxed text-ink-muted">{description}</div>
          ) : null}
        </div>
        {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
      </header>
      {children}
    </div>
  )
}
