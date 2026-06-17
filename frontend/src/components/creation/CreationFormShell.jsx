/**
 * 创作表单布局。
 */
import { motion } from 'framer-motion'
import { cn } from '@/utils/cn'
import { pageEnter } from '@/constants/motion'

export default function CreationFormShell({ sidebar, main, aside, className }) {
  const hasSidebar = Boolean(sidebar)
  const hasAside = Boolean(aside)

  return (
    <motion.div
      {...pageEnter}
      className={cn(
        'relative z-10 grid min-h-[calc(100vh-4rem)] grid-cols-1',
        hasSidebar && 'lg:grid-cols-[320px_1fr]',
        hasSidebar && hasAside && 'xl:grid-cols-[320px_1fr_360px]',
        className,
      )}
    >
      {hasSidebar ? (
        <aside className="hidden border-r border-white/5 bg-slate-900/40 p-5 lg:block">{sidebar}</aside>
      ) : null}
      <main className={cn('min-w-0 overflow-auto p-6 md:p-7 lg:p-9', !hasSidebar && !hasAside && 'sf-page-shell max-w-5xl px-0')}>
        {main}
      </main>
      {hasAside ? (
        <aside className="hidden border-l border-white/5 bg-slate-900/40 p-5 xl:block">{aside}</aside>
      ) : null}
    </motion.div>
  )
}
