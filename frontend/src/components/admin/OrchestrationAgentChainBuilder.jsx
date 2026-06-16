import { useMemo } from 'react'
import { ArrowRight, GripVertical, Plus, X } from 'lucide-react'
import { cn } from '@/utils/cn'
import OrchestrationDraggableList from './OrchestrationDraggableList'

function agentLabel(agentId, agentsById = {}) {
  const agent = agentsById[agentId]
  return agent?.name_zh || agent?.name || agentId
}

/**
 * 后处理链可视化编排：从 Agent 池拖入/排序，替代逗号输入。
 */
export default function OrchestrationAgentChainBuilder({
  chain = [],
  appendAgents = [],
  agentsById = {},
  agentPool = [],
  onChainChange,
  onAppendChange,
  disabled = false,
}) {
  const poolItems = useMemo(() => {
    const inChain = new Set(chain)
    const inAppend = new Set(appendAgents)
    const fromPool = (agentPool || []).filter((a) => a?.id && !inChain.has(a.id))
    const fromRegistry = Object.values(agentsById || {})
      .filter((a) => a?.id && !inChain.has(a.id) && !inAppend.has(a.id))
      .map((a) => ({ id: a.id, name_zh: a.name_zh, name: a.name }))
    const merged = [...fromPool]
    for (const item of fromRegistry) {
      if (!merged.some((row) => row.id === item.id)) merged.push(item)
    }
    return merged.sort((a, b) => (a.name_zh || a.id).localeCompare(b.name_zh || b.id))
  }, [agentPool, agentsById, chain, appendAgents])

  function addToChain(agentId) {
    if (!agentId || chain.includes(agentId)) return
    onChainChange?.([...chain, agentId])
  }

  function removeFromChain(agentId) {
    onChainChange?.(chain.filter((id) => id !== agentId))
  }

  function addToAppend(agentId) {
    if (!agentId || appendAgents.includes(agentId)) return
    onAppendChange?.([...appendAgents, agentId])
  }

  function removeFromAppend(agentId) {
    onAppendChange?.(appendAgents.filter((id) => id !== agentId))
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="text-xs text-navy-400 mb-2">执行链（拖拽排序）</div>
        {chain.length === 0 ? (
          <p className="text-xs text-navy-400 py-3 px-3 rounded-xl border border-dashed border-white/5">
            从下方 Agent 池点击添加，或拖拽主链尾部节点
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            <OrchestrationDraggableList
              items={chain.map((id) => ({ id }))}
              getId={(row) => row.id}
              onReorder={(ids) => onChainChange?.(ids)}
              disabled={disabled}
              className="flex flex-wrap gap-2 !space-y-0"
              renderItem={(row) => (
                <span className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-navy-100">
                  <GripVertical className="w-3 h-3 text-navy-500" />
                  {agentLabel(row.id, agentsById)}
                  <button
                    type="button"
                    onClick={() => removeFromChain(row.id)}
                    className="text-navy-400 hover:text-red-300"
                    aria-label="移除"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
            />
          </div>
        )}
      </div>

      <div>
        <div className="text-xs text-navy-400 mb-2">完成后追加 Agent</div>
        <div className="flex flex-wrap gap-2 min-h-[2rem]">
          {appendAgents.map((agentId) => (
            <span
              key={agentId}
              className="inline-flex items-center gap-1.5 rounded-xl border border-dashed border-white/10 bg-white/[0.02] px-3 py-1.5 text-xs text-navy-200"
            >
              {agentLabel(agentId, agentsById)}
              <button
                type="button"
                onClick={() => removeFromAppend(agentId)}
                className="text-navy-400 hover:text-red-300"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          {appendAgents.length === 0 ? (
            <span className="text-xs text-navy-400">可选，如 marketing</span>
          ) : null}
        </div>
      </div>

      <div className="pt-2 border-t border-white/10">
        <div className="text-xs text-navy-400 mb-2">Agent 池（点击加入链或追加）</div>
        <div className="flex flex-wrap gap-2">
          {poolItems.map((agent) => (
            <div key={agent.id} className="inline-flex overflow-hidden rounded-xl border border-white/10">
              <button
                type="button"
                disabled={disabled}
                onClick={() => addToChain(agent.id)}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs text-navy-200 hover:bg-white/[0.06] disabled:opacity-40"
                title="加入执行链"
              >
                <Plus className="w-3 h-3 text-gold-400" />
                {agent.name_zh || agent.name || agent.id}
              </button>
              <button
                type="button"
                disabled={disabled}
                onClick={() => addToAppend(agent.id)}
                className="border-l border-white/10 px-2 py-1.5 text-[10px] text-navy-400 hover:text-gold-300 disabled:opacity-40"
                title="加入追加"
              >
                追加
              </button>
            </div>
          ))}
          {poolItems.length === 0 ? (
            <span className="text-xs text-navy-400">无可用 Agent</span>
          ) : null}
        </div>
      </div>
    </div>
  )
}

export function OrchestrationChainPreview({ chain = [], agentsById = {}, className }) {
  if (!chain.length) return null
  return (
    <div className={cn('flex flex-wrap items-center gap-1.5', className)}>
      {chain.map((agentId, index) => (
        <span key={`${agentId}-${index}`} className="flex items-center gap-1">
          <span className="rounded-lg border border-dashed border-white/10 bg-white/[0.02] px-2.5 py-1 text-[11px] text-slate-300">
            {agentLabel(agentId, agentsById)}
          </span>
          {index < chain.length - 1 ? <ArrowRight className="w-3 h-3 text-navy-500" /> : null}
        </span>
      ))}
    </div>
  )
}
