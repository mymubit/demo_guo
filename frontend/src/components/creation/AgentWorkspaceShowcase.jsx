import { Bot } from 'lucide-react'
import { cn } from '@/utils/cn'

export default function AgentWorkspaceShowcase({ agents = [], hint = '', compact = false }) {
  const rows = [...agents].sort((a, b) => (a.workspace_order || 0) - (b.workspace_order || 0))

  if (!rows.length) return null

  return (
    <div
      className={cn(
        'rounded-2xl border border-white/5 bg-slate-900/50',
        compact ? 'px-4 py-4' : 'px-5 py-5',
      )}
    >
      <div className="mb-3 flex items-center gap-2">
        <Bot className="h-4 w-4 text-gold-400" />
        <h3 className="text-sm font-semibold text-white">独立 Agent 工作台</h3>
      </div>
      <p className="text-xs leading-relaxed text-navy-300">
        {hint || '提交后进入工作台，由你手动逐个运行 Agent，不会自动执行主链流水线。'}
      </p>
      <div className={cn('mt-4 grid gap-2', compact ? 'sm:grid-cols-2' : 'sm:grid-cols-2 lg:grid-cols-4')}>
        {rows.map((agent) => (
          <div
            key={agent.agent_id}
            className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3"
          >
            <div className="text-sm font-medium text-white">{agent.name_zh || agent.name}</div>
            <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-navy-400">
              {agent.description}
            </p>
            {(agent.output_artifacts || []).length ? (
              <p className="mt-2 text-[10px] text-navy-500">
                输出：{(agent.output_artifacts || []).join('、')}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  )
}
