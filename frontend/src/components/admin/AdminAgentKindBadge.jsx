import { cn } from '@/utils/cn'

/** Agent 类型标签：流水线 / 填表 / 后处理 / 辅助 */
export const AGENT_KIND_META = {
  pipeline: {
    label: '流水线',
    className: 'border-purple-500/30 bg-purple-500/10 text-purple-200',
  },
  form: {
    label: '填表',
    className: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-200',
  },
  post: {
    label: '后处理',
    className: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
  },
  auxiliary: {
    label: '辅助',
    className: 'border-slate-500/40 bg-slate-800/50 text-navy-300',
  },
}

export default function AdminAgentKindBadge({ kind = 'pipeline', className }) {
  const meta = AGENT_KIND_META[kind] || AGENT_KIND_META.pipeline
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium border',
        meta.className,
        className,
      )}
    >
      {meta.label} Agent
    </span>
  )
}
