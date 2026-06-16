/**
 * 创作模式说明 — 分步掌控 vs 技能工作台的后处理路径差异。
 */
export default function MainChainExecutionModesCard({ blueprint }) {
  const modes = blueprint?.execution_modes
  if (!modes?.step && !modes?.workspace) return null

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {modes.step ? (
        <div className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3">
          <div className="text-sm font-medium text-navy-100">{modes.step.label || '分步掌控'}</div>
          <p className="text-xs text-navy-400 mt-1 leading-relaxed">{modes.step.hint}</p>
          {modes.step.pipeline_tail_indices?.length ? (
            <p className="text-[11px] text-navy-300 mt-2 font-mono">
              管线节点：{modes.step.pipeline_tail_indices.join(' → ')}
            </p>
          ) : null}
        </div>
      ) : null}
      {modes.workspace ? (
        <div className="rounded-xl border border-gold-500/20 bg-gold-500/5 px-4 py-3">
          <div className="text-sm font-medium text-gold-200/90">{modes.workspace.label || '技能工作台'}</div>
          <p className="text-xs text-navy-400 mt-1 leading-relaxed">{modes.workspace.hint}</p>
        </div>
      ) : null}
    </div>
  )
}
