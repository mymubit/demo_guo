import { useEffect, useState } from 'react'
import { Save } from 'lucide-react'
import OrchestrationAgentChainBuilder from '@/components/admin/OrchestrationAgentChainBuilder'

export default function OrchestrationPostScriptPanel({ blueprint, onSave, saving = false }) {
  const [chain, setChain] = useState([])
  const [appendAgents, setAppendAgents] = useState([])
  const [polishRounds, setPolishRounds] = useState(2)
  const [dirty, setDirty] = useState(false)

  const agentsById = blueprint?.agents || {}
  const agentPool = blueprint?.catalog?.postScriptAgents || []

  useEffect(() => {
    setChain(blueprint?.post_script_chain || [])
    setAppendAgents(blueprint?.post_script_append_agents || [])
    setPolishRounds(blueprint?.polish_max_rounds ?? 2)
    setDirty(false)
  }, [
    blueprint?.post_script_chain,
    blueprint?.post_script_append_agents,
    blueprint?.polish_max_rounds,
  ])

  async function handleSave() {
    await onSave?.({
      post_script_chain: chain,
      post_script_append_agents: appendAgents,
      polish_max_rounds: polishRounds,
      flow_graph: blueprint?.flow_graph || { edges: [], parallel_groups: [] },
    })
    setDirty(false)
  }

  return (
    <details className="sf-console-panel group" open>
      <summary className="cursor-pointer list-none px-5 py-4 flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-white">后处理链（技能工作台模式）</div>
          <p className="text-xs text-navy-400 mt-1">
            剧本全量生成后由此 Agent 链统一执行；拖拽排序，勿与分步模式节点 6/7 混用
          </p>
        </div>
        <span className="text-xs text-navy-400 group-open:rotate-180 transition-transform">▼</span>
      </summary>
      <div className="px-5 pb-5 space-y-4 border-t border-white/10 pt-4">
        <OrchestrationAgentChainBuilder
          chain={chain}
          appendAgents={appendAgents}
          agentsById={agentsById}
          agentPool={agentPool}
          onChainChange={(next) => {
            setChain(next)
            setDirty(true)
          }}
          onAppendChange={(next) => {
            setAppendAgents(next)
            setDirty(true)
          }}
          disabled={saving}
        />

        <label className="block text-sm text-navy-300 max-w-xs">
          Polish 最大轮次
          <input
            type="number"
            min={0}
            className="sf-control mt-1.5 max-w-[8rem]"
            value={polishRounds}
            onChange={(e) => {
              setPolishRounds(Number(e.target.value) || 0)
              setDirty(true)
            }}
          />
        </label>

        <div className="flex justify-end">
          <button
            type="button"
            disabled={!dirty || saving}
            onClick={handleSave}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm border border-gold-400/30 disabled:opacity-40"
          >
            <Save className="w-4 h-4" />
            {saving ? '保存中…' : '保存后处理链'}
          </button>
        </div>
      </div>
    </details>
  )
}
