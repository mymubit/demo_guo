import { ChevronRight } from 'lucide-react'
import { AdminBadge } from '@/components/admin/AdminUI'
import SubSkillStepBar from '@/components/admin/SubSkillStepBar'
import {
  mergeSubSkillSteps,
  resolveAgentSubSkills,
  runStatusLabel,
  summarizeSubSkillSteps,
} from '@/utils/agentExecutionLabels'

function fmtDuration(ms) {
  if (ms == null || ms < 0) return ''
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const RUN_TONE = {
  completed: 'success',
  failed: 'danger',
  running: 'warning',
}

export default function AgentTimelineCard({
  title,
  subtitle,
  agentId,
  catalog,
  executionTrace = [],
  dbRun,
  onInspectRun,
  defaultExpanded = false,
}) {
  const registrySkills = resolveAgentSubSkills(agentId, catalog)
  const steps = mergeSubSkillSteps(registrySkills, executionTrace)
  const { counts, firstFailed } = summarizeSubSkillSteps(steps)

  const derivedStatus = firstFailed
    ? 'failed'
    : counts.executed > 0 && counts.pending === 0
      ? 'completed'
      : counts.executed > 0
        ? 'running'
        : counts.skipped > 0
          ? 'skipped'
          : 'pending'

  const runStatus = dbRun?.status || derivedStatus
  const tone = RUN_TONE[runStatus] || 'default'

  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/40 overflow-hidden">
      <div className="px-4 py-3 border-b border-white/5 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-white">{title}</p>
          {subtitle ? <p className="text-[11px] text-navy-400 mt-0.5">{subtitle}</p> : null}
          <p className="text-[10px] text-navy-400 mt-1">
            子技能 {steps.length} 步
            {counts.executed ? ` · 已执行 ${counts.executed}` : ''}
            {counts.failed ? ` · 失败 ${counts.failed}` : ''}
            {counts.skipped ? ` · 跳过 ${counts.skipped}` : ''}
            {counts.pending ? ` · 未跑到 ${counts.pending}` : ''}
          </p>
        </div>
        <AdminBadge tone={tone}>{runStatusLabel(runStatus)}</AdminBadge>
      </div>

      <div className="px-4 py-3">
        <SubSkillStepBar steps={steps} compact={false} />
        {firstFailed?.message && !dbRun?.error_message ? (
          <p className="text-xs text-red-300/90 mt-2">失败原因：{firstFailed.message}</p>
        ) : null}
      </div>

      {dbRun ? (
        <button
          type="button"
          onClick={() => onInspectRun?.(dbRun.id)}
          className="w-full flex items-center justify-between gap-2 px-4 py-2.5 text-left text-xs border-t border-white/5 bg-slate-900/40 hover:bg-white/[0.05] transition"
        >
          <span className="text-navy-300">
            DB 记录 · {runStatusLabel(dbRun.status)}
            {dbRun.duration_ms != null ? ` · ${fmtDuration(dbRun.duration_ms)}` : ''}
            {dbRun.started_at
              ? ` · ${new Date(dbRun.started_at).toLocaleString()}`
              : ''}
          </span>
          <span className="inline-flex items-center gap-1 text-gold-400 shrink-0">
            查看详情
            <ChevronRight className="w-3.5 h-3.5" />
          </span>
        </button>
      ) : null}

      {dbRun?.error_message ? (
        <p className="px-4 pb-3 text-xs text-red-300/90">{dbRun.error_message}</p>
      ) : null}
    </div>
  )
}
