import { ArrowRight, GitFork } from 'lucide-react'
import { Link } from 'react-router-dom'

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
          ? 'bg-violet-400/20 border-violet-400/50 text-violet-100 ring-1 ring-violet-400/30'
          : 'bg-violet-900/30 border-violet-700/40 text-violet-200 hover:border-violet-600/60'
        : active
          ? 'bg-gold-400/20 border-gold-400/50 text-gold-100 ring-1 ring-gold-400/30'
          : 'bg-navy-800/60 border-navy-700/40 text-navy-200 hover:border-navy-600'
    return [
      stepClass,
      variantCls,
      step.enabled === false ? 'opacity-45' : '',
    ].join(' ')
  }

  const hasFork = tailSteps.length > 0 || postChain.length > 0

  return (
    <div
      className={`space-y-3 ${
        compact ? '' : 'p-4 rounded-2xl border border-navy-700/30 bg-navy-900/30'
      }`}
    >
      <div className="flex flex-wrap items-center gap-1.5">
        {steps.map((step, index) => (
          <span key={step.node_id} className="flex items-center gap-1.5">
            <button type="button" onClick={() => onSelectStep?.(step)} className={stepClasses(step, 'main')}>
              <span className="text-gold-400/90 mr-1">{step.node_index ?? index + 1}</span>
              {step.agent_name_zh || step.display_name || step.node_id}
              {step.coin_cost != null ? (
                <span className="text-navy-500 ml-1">· {step.coin_cost}币</span>
              ) : null}
            </button>
            {index < steps.length - 1 ? (
              <ArrowRight className="w-3 h-3 text-navy-600 shrink-0" />
            ) : null}
          </span>
        ))}

        <Link
          to="/admin/agent?tab=registry"
          className="ml-auto text-[11px] text-navy-500 hover:text-gold-300 transition-colors"
        >
          完整 Registry →
        </Link>
      </div>

      {hasFork ? (
        <div className="flex flex-wrap items-start gap-3 pt-1 border-t border-navy-800/50">
          <GitFork className="w-3.5 h-3.5 text-navy-600 mt-1 shrink-0" />
          {tailSteps.length > 0 ? (
            <div className="flex flex-wrap items-center gap-1.5 min-w-0">
              <span
                className="text-[10px] text-violet-400/90 uppercase tracking-wide shrink-0"
                title={blueprint?.execution_modes?.step?.hint}
              >
                分步尾部
              </span>
              {tailSteps.map((step, index) => (
                <span key={step.node_id} className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => onSelectStep?.(step)}
                    className={stepClasses(step, 'tail')}
                  >
                    <span className="mr-1 opacity-80">{step.node_index}</span>
                    {step.agent_name_zh || step.display_name || step.node_id}
                  </button>
                  {index < tailSteps.length - 1 ? (
                    <ArrowRight className="w-3 h-3 text-navy-600 shrink-0" />
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
              <span
                className="text-[10px] text-navy-500 uppercase tracking-wide shrink-0"
                title={blueprint?.execution_modes?.workspace?.hint}
              >
                工作台后处理
              </span>
              {postChain.map((agentId, index) => (
                <span key={`${agentId}-${index}`} className="flex items-center gap-1">
                  <span
                    className={`${stepClass} bg-navy-900/40 border-dashed border-navy-600/50 text-navy-300 cursor-default`}
                  >
                    {postLabelById[agentId] || agentId}
                  </span>
                  {index < postChain.length - 1 ? (
                    <ArrowRight className="w-3 h-3 text-navy-600 shrink-0" />
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
