import { useMemo } from 'react'
import { EChart, buildRhythmCurveOption, formatRhythmEpisodeLabel } from '@/components/charts'
import EmptyState from '@/components/ui/EmptyState'

export default function RhythmCurveChart({ curve = [], showSummaryGrid = true }) {
  const option = useMemo(() => buildRhythmCurveOption({ curve }), [curve])

  if (!option) {
    return (
      <EmptyState
        compact
        title="暂无节奏曲线数据"
        description="生成结构节奏后将展示全剧情绪强度曲线。"
        className="mb-5"
      />
    )
  }

  return (
    <div className="mb-5 rounded-2xl border border-white/5 bg-slate-900/40 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs text-navy-400">全剧情绪强度曲线</div>
        <div className="text-[10px] text-navy-400">悬停查看推荐钩子 · 纵轴 1–10</div>
      </div>
      <EChart option={option} height={240} />
      {showSummaryGrid ? (
        <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2">
          {curve.map((block, index) => (
            <div
              key={block.episodeRange || block.episodeGroup || block.episodeStart || index}
              className="rounded-lg border border-white/5 bg-slate-900/40 px-2.5 py-2 text-center"
            >
              <div className="text-[10px] text-navy-400">{formatRhythmEpisodeLabel(block)}</div>
              <div className="text-sm font-semibold text-gold-400">{block.intensityLevel ?? '—'}/10</div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}
