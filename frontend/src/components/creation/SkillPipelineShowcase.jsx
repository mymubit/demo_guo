import { motion } from 'framer-motion'
import { ChevronRight, Zap } from 'lucide-react'
import { nodeCoinCost } from '@/utils/number'
import { filterCreationPipelineNodes, displayPipelineStepName } from '@/utils/pipelineNodes'

function PipelineStepCard({ node, index }) {
  const Icon = node.icon
  const name = displayPipelineStepName(node.name)

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="group flex items-center gap-3 rounded-xl border border-navy-700/35 bg-navy-950/45 p-4 hover:border-purple-500/30 hover:bg-navy-900/55 transition-colors"
    >
      <div className="shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500/30 to-purple-600/10 border border-purple-400/20 flex items-center justify-center text-sm font-bold text-purple-100">
        {index + 1}
      </div>
      <div className="min-w-0 flex-1 flex items-center gap-2">
        {Icon ? <Icon className="w-4 h-4 text-gold-400 shrink-0" /> : null}
        <h4 className="text-sm font-semibold text-white leading-snug">{name}</h4>
      </div>
    </motion.div>
  )
}

function CompactPipelineStrip({ nodes, prefilledSteps = [] }) {
  const prefilled = new Set(prefilledSteps || [])
  return (
    <div className="rounded-xl border border-navy-700/30 bg-navy-950/35 px-3 py-3">
      <p className="text-[11px] text-navy-500 mb-2 tracking-wide">Agent 流水线 · {nodes.length} 步顺序执行</p>
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
                    : 'border-navy-700/40 bg-navy-900/50'
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
              </div>
              {idx < nodes.length - 1 ? (
                <ChevronRight className="w-3.5 h-3.5 text-navy-600 mx-0.5 shrink-0" />
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
}) {
  const visibleNodes =
    variant === 'creation' ? filterCreationPipelineNodes(nodes) : nodes || []

  if (!visibleNodes.length) return null

  const totalCost = showTotalCost
    ? visibleNodes.reduce((sum, n) => sum + (nodeCoinCost(n) || 0), 0)
    : 0

  if (compact) {
    return <CompactPipelineStrip nodes={visibleNodes} prefilledSteps={prefilledSteps} />
  }

  return (
    <div className="glass-card rounded-2xl border border-navy-700/40 overflow-hidden">
      <div className="px-6 py-5 border-b border-navy-700/30 bg-gradient-to-r from-purple-500/10 via-navy-900/20 to-gold-500/5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 text-purple-300 text-xs font-medium mb-1">
              <Zap className="w-3.5 h-3.5" />
              创作 Agent 链
            </div>
            <h3 className="text-lg font-bold text-white">
              {visibleNodes.length} 个创作 Agent · 依次自动执行
            </h3>
            <p className="text-sm text-navy-400 mt-1">
              Brief → World → Character → Outline → Script，后接质检与宣发 Agent
            </p>
          </div>
          {showTotalCost && totalCost > 0 ? (
            <div className="inline-flex items-baseline gap-1.5 self-start px-4 py-2.5 rounded-xl bg-gold-500/10 border border-gold-500/25">
              <span className="text-xs text-navy-400">全流程约</span>
              <span className="text-2xl font-bold text-gold-400">{totalCost}</span>
              <span className="text-sm text-navy-300">{currencyName}</span>
            </div>
          ) : null}
        </div>
      </div>

      <div className="p-5 sm:p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {visibleNodes.map((node, idx) => (
            <PipelineStepCard
              key={node.fusion_node_id || node.index || idx}
              node={node}
              index={idx}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
