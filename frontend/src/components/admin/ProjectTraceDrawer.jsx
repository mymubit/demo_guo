import { Link } from 'react-router-dom'
import { X, ExternalLink } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'
import { ProjectAgentTraceView } from '@/components/admin/ProjectAgentTrace'

/** 创作项目列表侧滑：快速查看轨迹，可跳转完整监察页 */
export default function ProjectTraceDrawer({ projectId, onClose }) {
  if (!projectId) return null

  const fullUrl = `/admin/creation/projects/${projectId}/trace`

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex justify-end bg-black/50"
        onClick={onClose}
      >
        <motion.aside
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 28, stiffness: 320 }}
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-xl h-full bg-navy-950 border-l border-navy-700/40 shadow-2xl flex flex-col"
        >
          <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-navy-700/40 shrink-0">
            <div>
              <h2 className="text-lg font-semibold text-white">项目轨迹</h2>
              <p className="text-xs text-navy-500 mt-0.5">侧栏预览 · 完整复核请打开监察页</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-navy-400 hover:text-white hover:bg-navy-800/50"
              aria-label="关闭"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-4">
            <ProjectAgentTraceView projectId={projectId} compact showSummary />
          </div>

          <div className="shrink-0 px-5 py-4 border-t border-navy-700/40 flex flex-wrap gap-3">
            <Link
              to={fullUrl}
              onClick={onClose}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gold-500/15 text-gold-300 border border-gold-500/30 text-sm font-medium hover:bg-gold-500/25"
            >
              <ExternalLink className="w-4 h-4" />
              打开完整监察页
            </Link>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl text-sm text-navy-300 border border-navy-600/40 hover:bg-navy-800/50"
            >
              关闭
            </button>
          </div>
        </motion.aside>
      </motion.div>
    </AnimatePresence>
  )
}
