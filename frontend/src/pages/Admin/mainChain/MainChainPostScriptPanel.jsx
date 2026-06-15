import { useEffect, useState } from 'react'
import { Save } from 'lucide-react'
import { csvToList, listToCsv } from '@/components/admin/AgentConfigEditors'

const inputCls =
  'mt-1 w-full rounded-xl bg-navy-950 border border-navy-700 px-3 py-2 text-white text-sm focus:border-gold-500/40 outline-none'

export default function MainChainPostScriptPanel({ blueprint, onSave, saving = false }) {
  const [chain, setChain] = useState([])
  const [appendAgents, setAppendAgents] = useState([])
  const [polishRounds, setPolishRounds] = useState(2)
  const [dirty, setDirty] = useState(false)

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

  function markDirty() {
    setDirty(true)
  }

  async function handleSave() {
    await onSave?.({
      post_script_chain: chain,
      post_script_append_agents: appendAgents,
      polish_max_rounds: polishRounds,
    })
    setDirty(false)
  }

  return (
    <details className="glass-card rounded-2xl border border-navy-700/40 overflow-hidden group">
      <summary className="cursor-pointer list-none px-5 py-4 flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-white">后处理链（剧本全量生成后）</div>
          <p className="text-xs text-navy-500 mt-1">
            技能工作台：剧本全量后由此链统一执行质检/评分等（勿与分步模式节点 6/7 混用）
          </p>
          {blueprint?.execution_modes?.workspace?.hint ? (
            <p className="text-[11px] text-navy-600 mt-1">{blueprint.execution_modes.workspace.hint}</p>
          ) : null}
        </div>
        <span className="text-xs text-navy-500 group-open:rotate-180 transition-transform">▼</span>
      </summary>
      <div className="px-5 pb-5 space-y-4 border-t border-navy-800/60 pt-4">
        <label className="block text-sm text-navy-300">
          post_script_chain（逗号分隔 agent id）
          <input
            className={inputCls}
            value={listToCsv(chain)}
            onChange={(e) => {
              setChain(csvToList(e.target.value))
              markDirty()
            }}
            placeholder="review, polish, review, score"
          />
        </label>
        <label className="block text-sm text-navy-300">
          完成后追加 Agent（post_script_append_agents）
          <input
            className={inputCls}
            value={listToCsv(appendAgents)}
            onChange={(e) => {
              setAppendAgents(csvToList(e.target.value))
              markDirty()
            }}
            placeholder="marketing"
          />
        </label>
        <label className="block text-sm text-navy-300 max-w-xs">
          Polish 最大轮次
          <input
            type="number"
            min={0}
            className={inputCls}
            value={polishRounds}
            onChange={(e) => {
              setPolishRounds(Number(e.target.value) || 0)
              markDirty()
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
