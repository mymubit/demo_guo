/**
 * 创作模式说明 — 分步掌控 vs 技能工作台的后处理路径差异。
 */
export default function MainChainExecutionModesCard({ blueprint }) {
  const modes = blueprint?.execution_modes
  if (!modes?.step && !modes?.workspace) return null

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {modes.step ? (
        <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 px-4 py-3">
          <div className="text-sm font-medium text-violet-200">{modes.step.label || '分步掌控'}</div>
          <p className="text-xs text-navy-400 mt-1 leading-relaxed">{modes.step.hint}</p>
          {modes.step.pipeline_tail_indices?.length ? (
            <p className="text-[11px] text-navy-500 mt-2 font-mono">
              管线节点：{modes.step.pipeline_tail_indices.join(' → ')}
            </p>
          ) : null}
        </div>
      ) : null}
      {modes.workspace ? (
        <div className="rounded-xl border border-navy-600/30 bg-navy-900/30 px-4 py-3">
          <div className="text-sm font-medium text-navy-200">{modes.workspace.label || '技能工作台'}</div>
          <p className="text-xs text-navy-400 mt-1 leading-relaxed">{modes.workspace.hint}</p>
        </div>
      ) : null}
    </div>
  )
}
