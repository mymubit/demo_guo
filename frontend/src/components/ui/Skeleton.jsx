import { cn } from '@/utils/cn'

// 通用骨架块 — 矩形/方形占位
export function SkeletonBlock({
  className,
  rounded = 'rounded-xl',
  animate = true,
  style,
}) {
  return (
    <div
      className={cn(
        'bg-slate-800/60',
        rounded,
        animate && 'animate-pulse',
        className,
      )}
      style={style}
    />
  )
}

// 文本行骨架 — 模拟多行文本
export function SkeletonLines({
  lines = 3,
  lineHeight = 'h-3',
  gap = 'gap-2',
  className,
  widths,
}) {
  return (
    <div className={cn('flex flex-col', gap, className)}>
      {Array.from({ length: lines }).map((_, i) => {
        // 默认每行宽度递减，营造文本不齐的真实感
        const width = widths ? widths[i % widths.length] : 100 - Math.min(i * 12, 40)
        return (
          <div
            key={i}
            className={cn('bg-slate-800/60 rounded animate-pulse', lineHeight)}
            style={{ width: `${width}%` }}
          />
        )
      })}
    </div>
  )
}

// 卡片骨架 — 模拟卡片布局
export function SkeletonCard({ className, headerHeight = 'h-24', contentLines = 3 }) {
  return (
    <div className={cn('rounded-2xl border border-white/5 bg-slate-900/60 p-4', className)}>
      <div className={cn('rounded-xl bg-slate-800/60 animate-pulse mb-4', headerHeight)} />
      <SkeletonLines lines={contentLines} />
    </div>
  )
}

// 表格行骨架 — 模拟表格
export function SkeletonTableRow({ columns = 4, rowHeight = 'h-12' }) {
  return (
    <div className={cn('flex gap-3 py-3 border-b border-white/5 animate-pulse', rowHeight)}>
      {Array.from({ length: columns }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'rounded-lg bg-slate-800/50 flex-1',
            i === columns - 1 ? 'w-20 flex-none' : '',
          )}
        />
      ))}
    </div>
  )
}

// 页面骨架 — 包装整个页面加载状态
export function SkeletonPage({ className }) {
  return (
    <div className={cn('animate-fade-in', className)}>
      <SkeletonBlock className="h-10 w-48 mb-6" rounded="rounded-xl" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {[0, 1, 2].map(i => (
          <SkeletonCard key={i} headerHeight="h-16" contentLines={2} />
        ))}
      </div>
      <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4">
        <SkeletonBlock className="h-8 w-32 mb-4" rounded="rounded-lg" />
        <SkeletonBlock className="h-8 w-full mb-4" rounded="rounded-lg" />
        {[0, 1, 2, 3, 4].map(i => (
          <SkeletonTableRow key={i} columns={4} />
        ))}
      </div>
    </div>
  )
}

export default SkeletonBlock
