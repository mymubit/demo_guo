import type { CSSProperties, ReactNode } from 'react'
import { cn } from '@/utils/cn'

interface MasterDetailLayoutProps {
  aside: ReactNode
  detail: ReactNode
  asideWidth?: string
  className?: string
  asideClassName?: string
  detailClassName?: string
}

/** 全站主从分栏：左侧列表/表单，右侧详情/结果。 */
export function MasterDetailLayout({
  aside,
  detail,
  asideWidth = '22rem',
  className,
  asideClassName,
  detailClassName,
}: MasterDetailLayoutProps) {
  const gridStyle = {
    '--md-aside': asideWidth,
  } as CSSProperties

  return (
    <div
      className={cn(
        'grid min-h-[32rem] items-stretch gap-4 lg:grid-cols-[var(--md-aside)_minmax(0,1fr)]',
        className,
      )}
      style={gridStyle}
    >
      <aside className={cn('flex min-h-0 min-w-0 flex-col', asideClassName)}>
        <div className="flex min-h-[32rem] flex-1 flex-col">{aside}</div>
      </aside>
      <section className={cn('flex min-h-0 min-w-0 flex-col', detailClassName)}>
        <div className="flex min-h-[32rem] flex-1 flex-col">{detail}</div>
      </section>
    </div>
  )
}
