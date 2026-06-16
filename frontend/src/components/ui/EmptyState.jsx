import { motion } from 'framer-motion'
import { FolderOpen } from 'lucide-react'
import { ICON } from '@/constants/iconSizes'
import { cn } from '@/utils/cn'
import { cardEnter } from '@/constants/motion'

export default function EmptyState({
  icon: Icon = FolderOpen,
  title,
  description,
  action,
  size = 'md',
  compact = false,
  className = '',
}) {
  const isCompact = compact || size === 'sm'

  return (
    <motion.div
      {...cardEnter}
      className={cn(
        'rounded-2xl border border-white/5 bg-slate-900/60 text-center shadow-card',
        isCompact ? 'p-8' : 'p-10 md:p-14',
        className,
      )}
    >
      <div
        className={cn(
          'mx-auto rounded-2xl border border-white/10 bg-slate-800/50 flex items-center justify-center',
          isCompact ? 'mb-4 h-14 w-14' : 'mb-6 h-20 w-20',
        )}
      >
        <Icon className={cn(isCompact ? ICON.xl : ICON.empty, 'text-gold-400/80')} />
      </div>
      {title && (
        <h3 className={cn('font-bold text-white', isCompact ? 'text-lg mb-2' : 'text-2xl mb-3')}>
          {title}
        </h3>
      )}
      {description && (
        <p className={cn('mx-auto max-w-md text-navy-300', action ? 'mb-8' : '', isCompact && 'text-sm')}>
          {description}
        </p>
      )}
      {action}
    </motion.div>
  )
}
