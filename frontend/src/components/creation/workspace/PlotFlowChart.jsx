import { useMemo } from 'react'
import { EChart, buildPlotFlowGraphOption } from '@/components/charts'
import EmptyState from '@/components/ui/EmptyState'

export default function PlotFlowChart({ stageBlocks = [], episodes = [], height = 360 }) {
  const option = useMemo(
    () => buildPlotFlowGraphOption({ stageBlocks, episodes }),
    [stageBlocks, episodes],
  )

  if (!option) {
    return (
      <EmptyState
        compact
        title="暂无剧情脉络数据"
        description="生成分集大纲后将展示阶段与分集关联。"
        className="mb-4"
      />
    )
  }

  return (
    <div className="rounded-xl border border-white/5 bg-slate-900/40 p-3 mb-4">
      <div className="text-xs text-navy-400 mb-2">剧情脉络 · 阶段与分集关联</div>
      <EChart option={option} height={height} />
    </div>
  )
}
