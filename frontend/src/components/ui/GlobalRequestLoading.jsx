import { AnimatePresence, motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { useRequestUiStore } from '@/store/requestUiStore'
import { ICON } from '@/constants/iconSizes'

export default function GlobalRequestLoading() {
  const pendingCount = useRequestUiStore((state) => state.pendingCount)

  return (
    <AnimatePresence>
      {pendingCount > 0 ? (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          className="fixed left-1/2 top-5 z-[120] -translate-x-1/2 rounded-full border border-white/10 bg-slate-900/95 px-4 py-2 text-sm text-navy-100 shadow-modal"
        >
          <Loader2 className={`${ICON.md} mr-2 inline animate-spin text-gold-400`} />
          请求处理中…
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
