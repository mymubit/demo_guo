import { useMemo, useState } from 'react'
import { Bot, ChevronDown, ChevronRight, Sparkles } from 'lucide-react'
import { cn } from '@/utils/cn'
import OrchestrationDraggableList from '@/components/admin/OrchestrationDraggableList'
import { OrchestrationChainPreview } from '@/components/admin/OrchestrationAgentChainBuilder'

/**
 * 三级流程画布：调度节点 → Agent → 子技能（可拖拽重排主链顺序）。
 */
export default function OrchestrationFlowCanvas({
  steps = [],
  postScriptChain = [],
  agentsById = {},
  executionPlan = null,
  selectedNodeId,
  onSelectStep,
  onReorderSteps,
  reordering = false,
}) {
  const [expandedIds, setExpandedIds] = useState(() => new Set())

  const parallelMetaByNodeId = useMemo(() => {
    const map = {}
    const indexToNodeId = Object.fromEntries(
      steps.map((step) => [step.node_index, step.node_id]).filter(([idx]) => idx != null)
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

  function toggleExpand(nodeId) {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) next.delete(nodeId)
      else next.add(nodeId)
      return next
    })
  }

  function handleReorder(orderedIds) {
    onReorderSteps?.(orderedIds)
  }

  return (
    <div className="sf-console-panel p-5 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-base font-semibold text-white">三级流程画布</h3>
          <p className="text-xs text-navy-400 mt-1">
            调度 → Agent → 子技能 · 拖拽调整顺序 · 点击节点进入步骤配置
          </p>
        </div>
        {reordering ? (
          <span className="text-xs text-gold-400 animate-pulse">保存顺序中…</span>
        ) : null}
      </div>

      <OrchestrationDraggableList
        items={orderedSteps}
        getId={(step) => step.id}
        onReorder={handleReorder}
        disabled={reordering}
        renderItem={(step, { index }) => {
          const active = step.node_id === selectedNodeId
          const expanded = expandedIds.has(step.node_id)
          const subSkills = step.sub_skills || []
          const agentName = step.agent_name_zh || step.display_name || step.node_id

          return (
            <div
              className={cn(
                'rounded-xl border transition-colors overflow-hidden',
                active
                  ? 'border-gold-500/40 bg-gold-500/5 ring-1 ring-gold-500/20'
                  : 'border-white/10 bg-white/[0.03] hover:border-white/20',
                step.enabled === false && 'opacity-50',
              )}
            >
              <div className="flex items-center gap-2 px-3 py-2.5">
                <button
                  type="button"
                  onClick={() => toggleExpand(step.node_id)}
                  className="text-navy-400 hover:text-navy-300 shrink-0"
                  aria-label={expanded ? '收起' : '展开'}
                >
                  {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </button>
                <button
                  type="button"
                  onClick={() => onSelectStep?.(step)}
                  className="flex-1 min-w-0 text-left"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[10px] uppercase tracking-wide text-gold-400/80 font-medium">
                      调度
                    </span>
                    <span className="text-xs text-gold-300 tabular-nums">
                      {step.chain_order ?? index + 1}
                    </span>
                    <span className="text-sm text-white font-medium truncate">{agentName}</span>
                    {step.coin_cost != null ? (
                      <span className="text-xs text-navy-400">{step.coin_cost} 币</span>
                    ) : null}
                    {parallelMetaByNodeId[step.node_id] ? (
                      <span className="text-[10px] px-2 py-0.5 rounded-full border border-cyan-500/35 text-cyan-300/90 bg-cyan-500/10">
                        并行 · {parallelMetaByNodeId[step.node_id].label || '组'}
                      </span>
                    ) : null}
                  </div>
                </button>
              </div>

              {expanded ? (
                <div className="px-3 pb-3 space-y-2 border-t border-white/10 pt-2 ml-6">
                  <div className="flex items-start gap-2 rounded-lg border border-white/5 bg-slate-900/40 px-3 py-2">
                    <Bot className="w-3.5 h-3.5 text-gold-400 mt-0.5 shrink-0" />
                    <div className="min-w-0">
                      <div className="text-[10px] uppercase tracking-wide text-navy-400">Agent</div>
                      <div className="text-xs text-navy-200 font-mono truncate">
                        {step.agent_id || '—'}
                      </div>
                      {step.llm_provider_name ? (
                        <div className="text-[11px] text-navy-400 mt-0.5">
                          模型：{step.llm_provider_name}
                        </div>
                      ) : null}
                    </div>
                  </div>

                  <div className="rounded-lg border border-white/5 bg-slate-900/40 px-3 py-2">
                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-navy-400 mb-1.5">
                      <Sparkles className="w-3 h-3" />
                      子技能 ({subSkills.length})
                    </div>
                    {subSkills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {subSkills.map((skill, idx) => (
                          <span
                            key={skill.id || skill.key || `${step.node_id}-skill-${idx}`}
                            className="rounded-md border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[11px] text-navy-300"
                          >
                            {skill.name_zh || skill.name || skill.id || skill.key || `技能 ${idx + 1}`}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[11px] text-navy-400">未配置子技能</p>
                    )}
                  </div>
                </div>
              ) : null}
            </div>
          )
        }}
      />

      {executionPlan?.edges?.length > 0 ? (
        <div className="pt-3 border-t border-white/10">
          <div className="text-[10px] uppercase tracking-wide text-navy-400 mb-2">
            条件分支（{executionPlan.edges.length}）
          </div>
          <div className="flex flex-wrap gap-2">
            {executionPlan.edges.map((edge, index) => {
              const fromStep = steps.find((s) => s.node_id === edge.from)
              const toStep = steps.find((s) => s.node_id === edge.to)
              const cond = edge.condition?.kind || 'always'
              return (
                <span
                  key={`${edge.from}-${edge.to}-${index}`}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] border border-violet-500/30 bg-violet-500/10 text-violet-200"
                >
                  {fromStep?.agent_name_zh || edge.from}
                  <span className="text-navy-400">→</span>
                  {toStep?.agent_name_zh || edge.to}
                  <span className="text-violet-300/70">({cond})</span>
                </span>
              )
            })}
          </div>
        </div>
      ) : null}

      {postScriptChain.length > 0 ? (
        <div className="pt-3 border-t border-white/10">
          <div className="text-[10px] uppercase tracking-wide text-navy-400 mb-2">
            工作台后处理链
          </div>
          <OrchestrationChainPreview chain={postScriptChain} agentsById={agentsById} />
        </div>
      ) : null}
    </div>
  )
}
