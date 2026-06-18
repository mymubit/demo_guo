import { ArrowRight, MousePointerClick } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '@/utils/cn'

export default function MainChainBlueprintStrip({ blueprint, selectedNodeId, onSelectStep, compact = false }) {
  const steps = blueprint?.workspace_steps?.length
    ? blueprint.workspace_steps
    : (blueprint?.steps || []).filter((s) => (s.node_index || 0) <= 5)

  const explicitAgents = blueprint?.explicit_post_agents || blueprint?.catalog?.explicitPostAgents || []
  const postAgents = blueprint?.catalog?.postScriptAgents || []
  const postLabelById = Object.fromEntries(postAgents.map((a) => [a.id, a.name_zh || a.name || a.id]))

  const stepClass = compact
    ? 'px-2.5 py-1 rounded-lg text-[11px] border transition-colors cursor-pointer'
    : 'px-3 py-1.5 rounded-xl text-xs border transition-colors cursor-pointer'

  function stepClasses(step) {
    const active = step.node_id === selectedNodeId
    return cn(
      stepClass,
      active
        ? 'bg-gold-500/15 border-gold-500/40 text-gold-100 ring-1 ring-gold-500/25'
        : 'border-white/10 bg-white/[0.03] text-navy-200 hover:border-white/20',
      step.enabled === false && 'opacity-45',
    )
  }

  return (
    <div className={cn('space-y-3', !compact && 'pt-1')}>
      <div className="flex flex-wrap items-center gap-2">
        {steps.map((step, index) => (
          <span key={step.node_id} className="flex items-center gap-1.5">
            <button type="button" onClick={() => onSelectStep?.(step)} className={stepClasses(step)}>
              <span className="text-gold-400/90 mr-1 tabular-nums">{step.node_index ?? index + 1}</span>
              {step.agent_name_zh || step.display_name || step.node_id}
              {step.coin_cost != null ? (
                <span className="text-navy-400 ml-1">· {step.coin_cost}</span>
              ) : null}
            </button>
            {index < steps.length - 1 ? <ArrowRight className="w-3 h-3 text-navy-500 shrink-0" /> : null}
          </span>
        ))}

        <Link
          to="/admin/agent?tab=registry"
          className="ml-auto text-[11px] text-navy-400 hover:text-gold-300 transition-colors"
        >
          Registry
        </Link>
      </div>

      {explicitAgents.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-white/10">
          <MousePointerClick className="w-3.5 h-3.5 text-navy-500 shrink-0" />
          <span className="text-[10px] text-navy-400 uppercase tracking-wide shrink-0">显式后处理</span>
          {explicitAgents.map((agentId) => (
            <span
              key={agentId}
              className={cn(
                stepClass,
                'cursor-default border-dashed border-white/10 bg-white/[0.02] text-slate-300',
              )}
            >
              {postLabelById[agentId] || agentId}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  )
}
