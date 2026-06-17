import { motion } from 'framer-motion'
import { AlertTriangle, Loader2, RefreshCw, WifiOff } from 'lucide-react'
import Button from './Button'
import Card from './Card'
import EmptyState from './EmptyState'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'
import { cardEnter } from '@/constants/motion'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

export function PageLoading({ label = '加载中…', className }) {
  return (
    <div className={cn('flex min-h-[280px] items-center justify-center text-navy-300', className)}>
      <Loader2 className={cn(ICON.lg, 'mr-3 animate-spin text-gold-400')} />
      <span>{label}</span>
    </div>
  )
}

export function SkeletonBlock({ className }) {
  return <div className={cn('animate-pulse rounded-2xl bg-slate-800/55', className)} />
}

export function PageSkeleton({ rows = 3 }) {
  return (
    <div className="space-y-5">
      <SkeletonBlock className="h-24" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {Array.from({ length: rows }).map((_, index) => (
          <SkeletonBlock key={index} className="h-36" />
        ))}
      </div>
    </div>
  )
}

export function ErrorState({ title = '加载失败', description, type = 'error', onRetry, className }) {
  const icon = type === 'network' ? WifiOff : AlertTriangle

  return (
    <Card as={motion.div} {...cardEnter} className={cn('text-center', className)} padding="xl">
      <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-danger-500/30 bg-danger-500/10 text-danger-300">
        {renderLucideIcon(icon, ICON.xl)}
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      {description ? <p className="mx-auto mt-2 max-w-md text-sm text-navy-300">{description}</p> : null}
      {onRetry ? (
        <Button className="mt-6" variant="gold" iconLeft={<RefreshCw className={ICON.md} />} onClick={onRetry}>
          重试
        </Button>
      ) : null}
    </Card>
  )
}

export function AsyncState({ loading, skeleton, error, empty, emptyProps, onRetry, children }) {
  if (loading) return skeleton || <PageLoading />
  if (error) return <ErrorState description={error.message || String(error)} onRetry={onRetry} />
  if (empty) return <EmptyState title="暂无数据" description="当前没有可展示的内容" {...emptyProps} />
  return children
}
