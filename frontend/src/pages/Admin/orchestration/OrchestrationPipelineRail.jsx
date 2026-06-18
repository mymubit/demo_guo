import { useMemo } from 'react'
import { ChevronRight, MousePointerClick, Sparkles } from 'lucide-react'
import OrchestrationDraggableList from '@/components/admin/OrchestrationDraggableList'
import OrchestrationNodeStateBadge from '@/components/admin/OrchestrationNodeStateBadge'
import { cn } from '@/utils/cn'
import { resolveNodeRunState } from '@/utils/orchestrationNodeStates'

export default function OrchestrationPipelineRail({
  steps = [],
  explicitPostAgents = [],
  agentsById = {},
  executionPlan = null,
  selectedNodeId,
  highlightNodeId = '',
  nodeStates = null,
  onSelectStep,
  onReorderSteps,
  reordering = false,
}) {
  const parallelMetaByNodeId = useMemo(() => {
    const map = {}
    const indexToNodeId = Object.fromEntries(
      steps.map((step) => [step.node_index, step.node_id]).filter(([idx]) => idx != null),
    )
    for (const stage of executionPlan?.stages || []) {
      if (stage.type !== 'parallel') continue
      for (const idx of stage.indices || []) {
        const nodeId = indexToNodeId[idx]
        if (nodeId) map[nodeId] = stage
      }
    }
    return map
  }, [executionPlan, steps])

  const orderedSteps = useMemo(
    () => [...steps].sort((a, b) => (a.chain_order || 0) - (b.chain_order || 0)),
    [steps],
  )

  return (
    <div className="sf-console-panel flex flex-col h-full min-h-[520px] overflow-hidden">
      <div className="px-4 py-3 border-b shrink-0 border-white/5">
        <h3 className="text-sm font-semibold text-white">主链 5 步</h3>
        <p className="text-xs text-navy-400 mt-0.5">
          拖拽排序 · 点击编辑{reordering ? ' · 保存中' : ''}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2">
        <OrchestrationDraggableList
          items={orderedSteps}
          getId={(step) => step.id}
          onReorder={onReorderSteps}
          disabled={reordering}
          className="space-y-1"
          renderItem={(step, { index }) => {
            const active = step.node_id === selectedNodeId
            const highlighted = step.node_id === highlightNodeId && !active
            const runState = resolveNodeRunState(nodeStates, step.node_id)
            const agentName = step.agent_name_zh || step.display_name || step.node_id
            const subCount = (step.sub_skills || []).length
            const parallel = parallelMetaByNodeId[step.node_id]

            return (
              <button
                type="button"
                onClick={() => onSelectStep?.(step)}
                className={cn(
                  'group w-full text-left rounded-xl border px-3 py-2.5 transition-all',
                  active
                    ? 'border-gold-500/45 bg-gold-500/10'
                    : highlighted
                      ? 'border-gold-400/35 bg-gold-500/5 ring-1 ring-gold-400/25'
                      : 'border-white/5 bg-slate-900/40 hover:border-white/20 hover:bg-white/[0.06]',
                  runState === 'running' && !active && 'border-cyan-500/35',
                  runState === 'failed' && !active && 'border-red-500/30',
                  runState === 'completed' && !active && 'border-green-500/25',
                  step.enabled === false && 'opacity-45',
                )}
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className={cn(
                      'w-8 h-8 rounded-lg text-xs font-bold flex items-center justify-center shrink-0',
                      active ? 'bg-gold-500/25 text-gold-100' : 'bg-slate-800 text-slate-400',
                    )}
                  >
                    {step.chain_order ?? index + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-white truncate">{agentName}</div>
                    <div className="flex flex-wrap items-center gap-1.5 mt-0.5">
                      <OrchestrationNodeStateBadge state={runState} compact />
                      {step.coin_cost != null ? (
                        <span className="text-[11px] text-navy-400">{step.coin_cost}</span>
                      ) : null}
                      {subCount > 0 ? (
                        <span className="text-[11px] text-navy-400 inline-flex items-center gap-0.5">
                          <Sparkles className="w-2.5 h-2.5" />
                          {subCount} 技能
                        </span>
                      ) : null}
                      {parallel ? <span className="text-[10px] text-cyan-400/80">并行</span> : null}
                    </div>
                  </div>
                  <ChevronRight
                    className={cn(
                      'w-3.5 h-3.5 shrink-0',
                      active ? 'text-gold-400' : 'text-navy-500 group-hover:text-navy-300',
                    )}
                  />
                </div>
              </button>
            )
          }}
        />
      </div>

      {explicitPostAgents.length > 0 ? (
        <div className="shrink-0 border-t border-white/5 bg-slate-900/40 px-4 py-3">
          <div className="flex items-center gap-1.5 text-[10px] text-navy-400 mb-2">
            <MousePointerClick className="w-3 h-3" />
            显式后处理
          </div>
          <div className="flex flex-wrap gap-1.5">
            {explicitPostAgents.map((agentId) => {
              const agent = agentsById[agentId] || {}
              return (
                <span
                  key={agentId}
                  className="rounded-lg border border-white/10 bg-white/[0.03] px-2 py-1 text-[11px] text-navy-200"
                >
                  {agent.name_zh || agent.name || agentId}
                </span>
              )
            })}
          </div>
        </div>
      ) : null}
    </div>
  )
}
