import { ChevronRight, Zap } from 'lucide-react'
import { nodeCoinCost } from '@/utils/number'
import { filterCreationPipelineNodes, displayPipelineStepName } from '@/utils/pipelineNodes'
import { cn } from '@/utils/cn'

function PipelineStepCard({ node, index }) {
  const Icon = node.icon
  const name = displayPipelineStepName(node.name)

  return (
    <div
      className={cn(
        'group flex items-center gap-3 rounded-xl border px-3 py-2.5 transition-colors',
        'border-white/10 bg-white/[0.03] hover:border-gold-400/30 hover:bg-gold-400/5',
      )}
    >
      <div className="grid h-[22px] w-[22px] shrink-0 place-items-center rounded-md border border-white/10 bg-white/5 text-[11px] font-bold text-navy-300">
        {index + 1}
      </div>
      <div className="min-w-0 flex-1 flex items-center gap-2">
        {Icon ? <Icon className="w-4 h-4 text-gold-400 shrink-0" /> : null}
        <h4 className="text-sm font-semibold text-white leading-snug">{name}</h4>
      </div>
    </div>
  )
}

function CompactPipelineStrip({ nodes, prefilledSteps = [], executionPlan = null }) {
  const prefilled = new Set(prefilledSteps || [])
  const hasParallel = Boolean(executionPlan?.has_parallel)
  const hasBranches = Boolean(executionPlan?.has_branches)
  const caption =
    hasParallel && hasBranches
      ? '含并行组与条件分支'
      : hasParallel
        ? '含并行执行组'
        : hasBranches
          ? '含条件分支'
          : `${nodes.length} 步顺序执行`
  return (
    <div className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-3">
      <p className="text-[11px] text-navy-400 mb-2 tracking-wide">Agent 流水线 · {caption}</p>
      <div className="flex flex-wrap items-center gap-y-2 gap-x-1">
        {nodes.map((node, idx) => {
          const Icon = node.icon
          const name = displayPipelineStepName(node.name)
          const stepNo = idx + 1
          const isPrefilled = prefilled.has(stepNo)
          return (
            <div key={node.fusion_node_id || node.index || idx} className="flex items-center">
              <div
                className={`inline-flex items-center gap-1.5 rounded-lg border px-2 py-1.5 ${
                  isPrefilled
                    ? 'border-emerald-500/30 bg-emerald-500/10 opacity-90'
                    : 'border-white/10 bg-white/[0.03]'
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-md text-[10px] font-bold flex items-center justify-center ${
                    isPrefilled
                      ? 'bg-emerald-500/25 text-emerald-200'
                      : 'bg-purple-500/20 text-purple-200'
                  }`}
                >
                  {stepNo}
                </span>
                {Icon ? <Icon className={`w-3 h-3 ${isPrefilled ? 'text-emerald-300' : 'text-gold-400'}`} /> : null}
                <span className={`text-xs ${isPrefilled ? 'text-emerald-100' : 'text-navy-100'}`}>{name}</span>
                {isPrefilled ? (
                  <span className="text-[10px] text-emerald-400/90">已预填</span>
                ) : null}
                {node.orchestrationStageType === 'parallel' ? (
                  <span className="text-[10px] text-cyan-400/90">并行</span>
                ) : null}
                {node.orchestrationHasBranch ? (
                  <span className="text-[10px] text-violet-400/90">分支</span>
                ) : null}
              </div>
              {idx < nodes.length - 1 ? (
                <ChevronRight className="w-3.5 h-3.5 text-navy-500 mx-0.5 shrink-0" />
              ) : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}

/**
 * Agent 流水线 — C 端只展示步骤序号与名称，不暴露 schema / sub-skill 细节
 */
export default function SkillPipelineShowcase({
  nodes,
  currencyName = '创作币',
  compact = false,
  variant = 'creation',
  showTotalCost = false,
  prefilledSteps = [],
  executionPlan = null,
}) {
  const visibleNodes =
    variant === 'creation' ? filterCreationPipelineNodes(nodes) : nodes || []

  if (!visibleNodes.length) return null

  const totalCost = showTotalCost
    ? visibleNodes.reduce((sum, n) => sum + (nodeCoinCost(n) || 0), 0)
    : 0

  const hasParallel = Boolean(executionPlan?.has_parallel)
  const hasBranches = Boolean(executionPlan?.has_branches)
  const flowCaption =
    hasParallel && hasBranches
      ? '含并行组与条件分支'
      : hasParallel
        ? '含并行执行组'
        : hasBranches
          ? '含条件分支路由'
          : '依次自动执行'

  if (compact) {
    return (
      <CompactPipelineStrip
        nodes={visibleNodes}
        prefilledSteps={prefilledSteps}
        executionPlan={executionPlan}
      />
    )
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-white/5 bg-slate-900/60">
      <div className="border-b border-white/5 px-6 py-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="mb-1 inline-flex items-center gap-1.5 text-xs font-medium text-gold-400">
              <Zap className="h-3.5 w-3.5" />
              创作 Agent 链
            </div>
            <h3 className="text-lg font-bold text-white">
              {visibleNodes.length} 个创作 Agent · {flowCaption}
            </h3>
            <p className="mt-1 text-sm text-navy-400">
              Brief → World → Character → Outline → Script，后接质检与宣发 Agent
            </p>
          </div>
          {showTotalCost && totalCost > 0 ? (
            <div className="inline-flex items-baseline gap-1.5 self-start rounded-xl border border-gold-400/30 bg-gold-400/10 px-4 py-2.5">
              <span className="text-xs text-navy-400">全流程约</span>
              <span className="text-2xl font-bold text-gold-400">{totalCost}</span>
              <span className="text-sm text-navy-300">{currencyName}</span>
            </div>
          ) : null}
        </div>
      </div>

      <div className="space-y-1 p-4">
        {visibleNodes.map((node, idx) => (
          <PipelineStepCard
            key={node.fusion_node_id || node.index || idx}
            node={node}
            index={idx}
          />
        ))}
      </div>
    </div>
  )
}
