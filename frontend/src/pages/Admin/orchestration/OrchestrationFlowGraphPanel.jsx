import { useEffect, useMemo, useState } from 'react'
import OrchestrationFlowGraphCanvas from '@/components/admin/OrchestrationFlowGraphCanvas'
import { GitBranch, Plus, Save, Trash2 } from 'lucide-react'

const CONDITION_OPTIONS = [
  { value: 'always', label: '始终' },
  { value: 'review_passed', label: '质检通过' },
  { value: 'review_failed', label: '质检未通过' },
  { value: 'score_gte', label: '评分 ≥ 阈值' },
  { value: 'score_lt', label: '评分 < 阈值' },
]

function stepLabel(step) {
  return step.agent_name_zh || step.display_name || step.node_id
}

/**
 * 流程图元数据：并行组 + 条件分支边。
 */
export default function OrchestrationFlowGraphPanel({
  blueprint,
  onSave,
  saving = false,
  steps = [],
  nodeStates = null,
  selectedNodeId = '',
  onSelectNode,
}) {
  const [parallelGroups, setParallelGroups] = useState([])
  const [edges, setEdges] = useState([])
  const [dirty, setDirty] = useState(false)

  const panelSteps = steps.length ? steps : blueprint?.steps || []

  const stepOptions = useMemo(
    () =>
      [...panelSteps]
        .sort((a, b) => (a.chain_order || 0) - (b.chain_order || 0))
        .map((step) => ({ id: step.node_id, label: stepLabel(step) })),
    [panelSteps]
  )

  useEffect(() => {
    setParallelGroups(blueprint?.flow_graph?.parallel_groups || [])
    setEdges(blueprint?.flow_graph?.edges || [])
    setDirty(false)
  }, [blueprint?.flow_graph?.parallel_groups, blueprint?.flow_graph?.edges])

  function addGroup() {
    setParallelGroups((prev) => [
      ...prev,
      { id: `group-${prev.length + 1}`, label: `并行组 ${prev.length + 1}`, node_ids: [] },
    ])
    setDirty(true)
  }

  function updateGroup(groupId, patch) {
    setParallelGroups((prev) => prev.map((g) => (g.id === groupId ? { ...g, ...patch } : g)))
    setDirty(true)
  }

  function removeGroup(groupId) {
    setParallelGroups((prev) => prev.filter((g) => g.id !== groupId))
    setDirty(true)
  }

  function toggleNode(groupId, nodeId) {
    setParallelGroups((prev) =>
      prev.map((g) => {
        if (g.id !== groupId) return g
        const ids = new Set(g.node_ids || [])
        if (ids.has(nodeId)) ids.delete(nodeId)
        else ids.add(nodeId)
        return { ...g, node_ids: [...ids] }
      })
    )
    setDirty(true)
  }

  function addEdge() {
    const from = stepOptions[0]?.id || ''
    const to = stepOptions[1]?.id || stepOptions[0]?.id || ''
    setEdges((prev) => [
      ...prev,
      {
        from,
        to,
        type: 'branch',
        condition: { kind: 'review_passed' },
        label: '',
      },
    ])
    setDirty(true)
  }

  function updateEdge(index, patch) {
    setEdges((prev) => prev.map((edge, idx) => (idx === index ? { ...edge, ...patch } : edge)))
    setDirty(true)
  }

  function updateEdgeCondition(index, patch) {
    setEdges((prev) =>
      prev.map((edge, idx) =>
        idx === index ? { ...edge, condition: { ...(edge.condition || {}), ...patch } } : edge
      )
    )
    setDirty(true)
  }

  function removeEdge(index) {
    setEdges((prev) => prev.filter((_, idx) => idx !== index))
    setDirty(true)
  }

  async function handleSave() {
    await onSave?.({
      flow_graph: {
        ...(blueprint?.flow_graph || {}),
        parallel_groups: parallelGroups,
        edges,
      },
    })
    setDirty(false)
  }

  return (
    <div className="space-y-4">
      <div className="sf-console-panel p-4 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-medium text-white">流程图画布</div>
            <p className="text-xs text-navy-400 mt-1">Dagre 自动布局 · 点击节点可在上方主画布同步选中</p>
          </div>
        </div>
        <OrchestrationFlowGraphCanvas
          steps={panelSteps}
          flowGraph={blueprint?.flow_graph}
          executionPlan={blueprint?.execution_plan}
          nodeStates={nodeStates}
          selectedNodeId={selectedNodeId}
          onSelectNode={onSelectNode}
          height={300}
        />
      </div>

      <details className="sf-console-panel group" open>
        <summary className="cursor-pointer list-none px-5 py-4 flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-medium text-white">并行组</div>
            <p className="text-xs text-navy-400 mt-1">
              同组节点在分步模式下将依次自动执行，全部完成后才进入下一阶段
            </p>
          </div>
          <span className="text-xs text-navy-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="px-5 pb-5 space-y-4 border-t border-white/10 pt-4">
          {parallelGroups.length === 0 ? (
            <p className="text-xs text-navy-400">尚未定义并行组</p>
          ) : (
            parallelGroups.map((group) => (
              <div
                key={group.id}
                className="rounded-xl border border-white/5 bg-slate-900/40 p-4 space-y-3"
              >
                <div className="flex items-center gap-2">
                  <input
                    className="sf-control flex-1 text-sm"
                    value={group.label || ''}
                    onChange={(e) => updateGroup(group.id, { label: e.target.value })}
                    placeholder="并行组名称"
                  />
                  <button
                    type="button"
                    onClick={() => removeGroup(group.id)}
                    className="p-2 rounded-lg text-navy-400 hover:text-red-300 hover:bg-white/[0.06]"
                    aria-label="删除并行组"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {panelSteps.map((step) => {
                    const checked = (group.node_ids || []).includes(step.node_id)
                    return (
                      <label
                        key={`${group.id}-${step.node_id}`}
                        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs border cursor-pointer ${
                          checked
                            ? 'border-gold-500/40 bg-gold-500/10 text-gold-200'
                            : 'border-white/10 text-navy-300 hover:border-white/20'
                        }`}
                      >
                        <input
                          type="checkbox"
                          className="sr-only"
                          checked={checked}
                          onChange={() => toggleNode(group.id, step.node_id)}
                        />
                        {stepLabel(step)}
                      </label>
                    )
                  })}
                </div>
              </div>
            ))
          )}
          <button
            type="button"
            onClick={addGroup}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-navy-200 border border-white/10 hover:bg-white/[0.06]"
          >
            <Plus className="w-3.5 h-3.5" />
            添加并行组
          </button>
        </div>
      </details>

      <details className="sf-console-panel group">
        <summary className="cursor-pointer list-none px-5 py-4 flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-medium text-white flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-gold-400" />
              条件分支
            </div>
            <p className="text-xs text-navy-400 mt-1">
              配置从某节点出发的分支边；分步模式运行时按质检/评分结果选路
            </p>
          </div>
          <span className="text-xs text-navy-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="px-5 pb-5 space-y-3 border-t border-white/10 pt-4">
          {edges.length === 0 ? (
            <p className="text-xs text-navy-400">尚未定义分支边</p>
          ) : (
            edges.map((edge, index) => (
              <div
                key={`edge-${index}`}
                className="rounded-xl border border-white/5 bg-slate-900/40 p-3 grid gap-2 sm:grid-cols-[1fr_1fr_auto_auto_auto]"
              >
                <label className="text-xs text-navy-400">
                  从
                  <select
                    className="sf-control mt-1 text-sm"
                    value={edge.from || ''}
                    onChange={(e) => updateEdge(index, { from: e.target.value })}
                  >
                    {stepOptions.map((opt) => (
                      <option key={`from-${opt.id}`} value={opt.id}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs text-navy-400">
                  到
                  <select
                    className="sf-control mt-1 text-sm"
                    value={edge.to || ''}
                    onChange={(e) => updateEdge(index, { to: e.target.value })}
                  >
                    {stepOptions.map((opt) => (
                      <option key={`to-${opt.id}`} value={opt.id}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs text-navy-400">
                  类型
                  <select
                    className="sf-control mt-1 text-sm"
                    value={edge.type || 'branch'}
                    onChange={(e) => updateEdge(index, { type: e.target.value })}
                  >
                    <option value="branch">条件分支</option>
                    <option value="default">默认回退</option>
                    <option value="sequential">顺序</option>
                  </select>
                </label>
                <label className="text-xs text-navy-400">
                  条件
                  <select
                    className="sf-control mt-1 text-sm"
                    value={edge.condition?.kind || 'always'}
                    onChange={(e) => updateEdgeCondition(index, { kind: e.target.value })}
                    disabled={edge.type === 'default'}
                  >
                    {CONDITION_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="flex items-end gap-2">
                  {(edge.condition?.kind === 'score_gte' || edge.condition?.kind === 'score_lt') ? (
                    <label className="text-xs text-navy-400 flex-1">
                      阈值
                      <input
                        type="number"
                        min={0}
                        className="sf-control mt-1 text-sm"
                        value={edge.condition?.value ?? 80}
                        onChange={(e) =>
                          updateEdgeCondition(index, { value: Number(e.target.value) || 0 })
                        }
                      />
                    </label>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => removeEdge(index)}
                    className="p-2 rounded-lg text-navy-400 hover:text-red-300 hover:bg-white/[0.06]"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
          <div className="flex flex-wrap justify-between gap-2 pt-1">
            <button
              type="button"
              onClick={addEdge}
              disabled={stepOptions.length < 2}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-navy-200 border border-white/10 hover:bg-white/[0.06] disabled:opacity-40"
            >
              <Plus className="w-3.5 h-3.5" />
              添加分支边
            </button>
            <button
              type="button"
              disabled={!dirty || saving}
              onClick={handleSave}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm border border-gold-400/30 disabled:opacity-40"
            >
              <Save className="w-4 h-4" />
              {saving ? '保存中…' : '保存流程图'}
            </button>
          </div>
        </div>
      </details>
    </div>
  )
}
