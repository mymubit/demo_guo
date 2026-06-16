import { ArrowRight, GitFork } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '@/utils/cn'

/**
 * 主链蓝图画布 — 工作台五步 + 分步尾部 / 工作台后处理双路径。
 */
export default function MainChainBlueprintStrip({ blueprint, selectedNodeId, onSelectStep, compact = false }) {
  const steps = blueprint?.workspace_steps?.length
    ? blueprint.workspace_steps
    : (blueprint?.steps || []).filter((s) => (s.node_index || 0) <= 5)

  const tailSteps =
    blueprint?.pipeline_tail_steps?.length
      ? blueprint.pipeline_tail_steps
      : (blueprint?.steps || []).filter((s) => (s.node_index || 0) > 5)

  const postChain = blueprint?.post_script_chain || []
  const postAgents = blueprint?.catalog?.postScriptAgents || []
  const postLabelById = Object.fromEntries(
    postAgents.map((a) => [a.id, a.name_zh || a.name || a.id])
  )

  const stepClass = compact
    ? 'px-2.5 py-1 rounded-lg text-[11px] border transition-colors cursor-pointer'
    : 'px-3 py-1.5 rounded-xl text-xs border transition-colors cursor-pointer'

  function stepClasses(step, variant = 'main') {
    const active = step.node_id === selectedNodeId
    const variantCls =
      variant === 'tail'
        ? active
          ? 'bg-slate-700/60 border-gold-500/40 text-gold-100 ring-1 ring-gold-500/25'
          : 'border-white/10 bg-white/[0.03] text-navy-200 hover:border-white/20'
        : active
          ? 'bg-gold-500/15 border-gold-500/40 text-gold-100 ring-1 ring-gold-500/25'
          : 'border-white/10 bg-white/[0.03] text-navy-200 hover:border-white/20'
    return cn(stepClass, variantCls, step.enabled === false && 'opacity-45')
  }

  const hasFork = tailSteps.length > 0 || postChain.length > 0

  return (
    <div className={cn('space-y-3', !compact && 'pt-1')}>
      <div className="flex flex-wrap items-center gap-2">
        {steps.map((step, index) => (
          <span key={step.node_id} className="flex items-center gap-1.5">
            <button type="button" onClick={() => onSelectStep?.(step)} className={stepClasses(step, 'main')}>
              <span className="text-gold-400/90 mr-1 tabular-nums">{step.node_index ?? index + 1}</span>
              {step.agent_name_zh || step.display_name || step.node_id}
              {step.coin_cost != null ? (
                <span className="text-navy-400 ml-1">· {step.coin_cost}币</span>
              ) : null}
            </button>
            {index < steps.length - 1 ? (
              <ArrowRight className="w-3 h-3 text-navy-500 shrink-0" />
            ) : null}
          </span>
        ))}

        <Link
          to="/admin/agent?tab=registry"
          className="ml-auto text-[11px] text-navy-400 hover:text-gold-300 transition-colors"
        >
          Registry →
        </Link>
      </div>

      {hasFork ? (
        <div className="flex flex-wrap items-start gap-3 pt-2 border-t border-white/10">
          <GitFork className="w-3.5 h-3.5 text-navy-500 mt-1 shrink-0" />
          {tailSteps.length > 0 ? (
            <div className="flex flex-wrap items-center gap-1.5 min-w-0">
              <span className="text-[10px] text-navy-400 uppercase tracking-wide shrink-0">分步尾部</span>
              {tailSteps.map((step, index) => (
                <span key={step.node_id} className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => onSelectStep?.(step)}
                    className={stepClasses(step, 'tail')}
                  >
                    <span className="mr-1 opacity-80 tabular-nums">{step.node_index}</span>
                    {step.agent_name_zh || step.display_name || step.node_id}
                  </button>
                  {index < tailSteps.length - 1 ? (
                    <ArrowRight className="w-3 h-3 text-navy-500 shrink-0" />
                  ) : null}
                </span>
              ))}
            </div>
          ) : null}
          {tailSteps.length > 0 && postChain.length > 0 ? (
            <span className="text-navy-700 text-xs shrink-0">|</span>
          ) : null}
          {postChain.length > 0 ? (
            <div className="flex flex-wrap items-center gap-1.5 min-w-0">
              <span className="text-[10px] text-navy-400 uppercase tracking-wide shrink-0">后处理</span>
              {postChain.map((agentId, index) => (
                <span key={`${agentId}-${index}`} className="flex items-center gap-1">
                  <span
                    className={cn(
                      stepClass,
                      'cursor-default border-dashed border-white/10 bg-white/[0.02] text-slate-300'
                    )}
                  >
                    {postLabelById[agentId] || agentId}
                  </span>
                  {index < postChain.length - 1 ? (
                    <ArrowRight className="w-3 h-3 text-navy-500 shrink-0" />
                  ) : null}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
