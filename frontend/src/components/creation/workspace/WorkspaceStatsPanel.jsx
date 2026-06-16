/**
 * Agent 工作台右侧 — 进度 / 当前模块 / 快捷操作
 */
import { Loader2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui'
import { SideSectionTitle, KvRow } from '@/components/shared/ConsumerSection'
import { ICON } from '@/constants/iconSizes'
import { ExecutionDurationLabel } from '@/components/shared/ExecutionRunPanel'
import { cn } from '@/utils/cn'

export default function WorkspaceStatsPanel({
  workspace,
  activeSkill,
  completedCount = 0,
  confirmedCount = 0,
  totalSkills = 0,
  currencyName = '创作币',
  refreshing,
  onRefresh,
  agentTabName,
}) {
  const run = activeSkill?.execution_run
  const coinCost = activeSkill?.coin_cost ?? activeSkill?.estimated_coin_cost
  const progressPercent = totalSkills > 0 ? Math.round((completedCount / totalSkills) * 100) : 0
  const isPassed =
    activeSkill?.status !== 'failed' &&
    (
      activeSkill?.content_kind === 'agent_generated' ||
      (activeSkill?.index === 1 &&
        activeSkill?.has_content &&
        activeSkill?.content_kind === 'user_confirmed')
    )

  return (
    <>
      <SideSectionTitle>项目进度</SideSectionTitle>
      <div className="rounded-2xl border border-white/5 bg-white/[0.025] p-3">
        <div className="flex items-end justify-between gap-3">
          <div>
            <div className="text-[11px] text-navy-400">已完成模块</div>
            <div className="mt-1 text-2xl font-bold text-white">
              {completedCount}
              <span className="ml-1 text-sm font-medium text-navy-400">/ {totalSkills}</span>
            </div>
          </div>
          <span className="rounded-lg border border-gold-400/20 bg-gold-400/10 px-2 py-1 text-xs font-semibold text-gold-300">
            {progressPercent}%
          </span>
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-800">
          <div
            className="h-full rounded-full bg-gradient-to-r from-gold-500 to-amber-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-navy-400">
          <span>{workspace?.status_text || workspace?.status || '—'}</span>
          {confirmedCount > completedCount ? <span>{confirmedCount} 步有内容</span> : null}
        </div>
      </div>
      <div className="mt-3 space-y-1">
        {workspace?.overall_score != null ? (
          <KvRow label="综合评分" value={`${workspace.overall_score}`} />
        ) : null}
      </div>

      {activeSkill ? (
        <>
          <SideSectionTitle>当前模块</SideSectionTitle>
          <div className="rounded-2xl border border-white/5 bg-white/[0.025] p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-[11px] text-navy-400">模块</div>
                <div className="mt-1 truncate text-sm font-semibold text-white">{agentTabName(activeSkill)}</div>
              </div>
              <span
                className={cn(
                  'shrink-0 rounded-lg border px-2 py-1 text-xs font-semibold',
                  activeSkill.status === 'running'
                    ? 'border-gold-400/25 bg-gold-400/10 text-gold-300'
                    : activeSkill.status === 'failed'
                      ? 'border-red-400/25 bg-red-500/10 text-red-300'
                      : isPassed
                        ? 'border-green-400/20 bg-green-500/10 text-green-300'
                        : activeSkill.has_content
                          ? 'border-gold-400/20 bg-gold-400/10 text-gold-300'
                          : 'border-white/10 bg-white/[0.03] text-navy-400',
                )}
              >
                {activeSkill.status === 'running'
                  ? '生成中'
                  : activeSkill.status === 'failed'
                    ? '失败'
                    : isPassed
                      ? '已通过'
                      : activeSkill.has_content
                        ? '有内容'
                        : '待生成'}
              </span>
            </div>
          </div>
          <div className="mt-3 space-y-1">
            {coinCost != null ? <KvRow label="节点币价" value={`${coinCost} ${currencyName}`} /> : null}
            {run?.duration_ms != null && activeSkill.status !== 'running' ? (
              <div className="flex justify-between border-b border-dashed border-white/5 py-2 text-[13px]">
                <span className="text-navy-200">最近耗时</span>
                <ExecutionDurationLabel durationMs={run.duration_ms} className="text-white font-semibold" />
              </div>
            ) : null}
          </div>
        </>
      ) : null}

      <div className="mt-5">
        <Button
          variant="secondary"
          size="sm"
          className="w-full justify-center"
          iconLeft={refreshing ? <Loader2 className={`${ICON.sm} animate-spin`} /> : <RefreshCw className={ICON.sm} />}
          onClick={onRefresh}
          disabled={refreshing}
        >
          {refreshing ? '刷新中…' : '刷新工作台'}
        </Button>
      </div>
    </>
  )
}
