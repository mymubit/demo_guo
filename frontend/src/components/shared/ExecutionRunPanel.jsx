import StepStatusMark from '@/components/ui/StepStatusMark'
import SubSkillStepBar from '@/components/admin/SubSkillStepBar'
import { hasDebugPayload, LlmRunTracePanel } from '@/components/shared/PayloadInspector'
import {
  mergeSubSkillSteps,
  resolveAgentSubSkills,
  runStatusLabel,
} from '@/utils/agentExecutionLabels'
import { resolveSkillId } from '@/utils/skillTerm'

function runStatusClass(status) {
  if (status === 'completed') return 'text-green-400'
  if (status === 'failed') return 'text-red-400'
  if (status === 'running') return 'text-amber-300'
  return 'text-navy-300'
}

function traceStatusClass(status) {
  if (status === 'executed') return 'bg-green-500/15 text-green-400'
  if (status === 'failed') return 'bg-red-500/15 text-red-400'
  if (status === 'skipped') return 'bg-white/[0.05] text-slate-400'
  return 'bg-amber-500/15 text-amber-300'
}

export function fmtExecutionDuration(ms) {
  if (ms == null || ms < 0) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

/** C 端仅展示耗时 */
export function ExecutionDurationLabel({ durationMs, className = '' }) {
  if (durationMs == null) return null
  return (
    <span className={`text-xs text-navy-400 tabular-nums ${className}`}>
      耗时 {fmtExecutionDuration(durationMs)}
    </span>
  )
}

function SummaryBlock({ title, data }) {
  if (!data || !Object.keys(data).length) return null
  return (
    <details className="mt-2">
      <summary className="text-xs text-navy-400 cursor-pointer hover:text-navy-200">{title}</summary>
      <pre className="mt-1 overflow-x-auto whitespace-pre-wrap rounded-lg border border-white/5 bg-slate-900/40 p-2 text-[10px] text-navy-300">
        {JSON.stringify(data, null, 2)}
      </pre>
    </details>
  )
}

/** 紧凑 pills — 用户工作台等场景 */
export function ExecutionTracePills({ trace, compact = false }) {
  if (!trace?.length) return <span className="text-navy-400 text-xs">无轨迹</span>
  return (
    <div className={`flex flex-wrap gap-1.5 ${compact ? '' : 'mt-1'}`}>
      {trace.map((step) => (
        <span
          key={step.id || step.skill_id}
          title={[step.status, step.type, step.cli, step.message].filter(Boolean).join(' · ')}
          className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${traceStatusClass(step.status)}`}
        >
          {step.id || step.skill_id}
          {step.status === 'failed' || step.status === 'skipped' ? (
            <StepStatusMark status={step.status} className="w-3 h-3" />
          ) : null}
        </span>
      ))}
    </div>
  )
}

export default function ExecutionRunPanel({
  run,
  compact = false,
  className = '',
  catalog = null,
}) {
  if (!run) return null

  const trace = run.execution_trace || run.sub_skills || []
  const registrySkills = resolveAgentSubSkills(resolveSkillId(run), catalog)
  const steps = catalog ? mergeSubSkillSteps(registrySkills, trace) : null

  return (
    <div
      className={`rounded-xl border border-white/5 bg-slate-900/40 ${compact ? 'p-3' : 'p-4'} ${className}`}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
        <span className={`font-medium ${runStatusClass(run.status)}`}>
          {runStatusLabel(run.status)}
        </span>
        {run.duration_ms != null ? (
          <span className="text-navy-400">耗时 {fmtExecutionDuration(run.duration_ms)}</span>
        ) : null}
        {run.output_artifact_key ? (
          <span className="text-navy-400">产出 {run.output_artifact_key}</span>
        ) : null}
        {run.started_at ? (
          <span className="text-navy-400">{new Date(run.started_at).toLocaleString()}</span>
        ) : null}
      </div>

      {run.error_message ? (
        <p className="mt-2 text-xs text-red-300/90">{run.error_message}</p>
      ) : null}

      <div className={compact ? 'mt-2' : 'mt-3'}>
        <p className="text-[10px] text-navy-400 mb-1">子技能步骤</p>
        {steps?.length ? (
          <SubSkillStepBar steps={steps} compact={compact} />
        ) : (
          <ExecutionTracePills trace={trace} compact />
        )}
      </div>

      {!compact ? (
        <>
          <SummaryBlock title="输入摘要" data={run.input_summary} />
          <SummaryBlock title="输出摘要" data={run.output_summary} />
          {(run.sub_skills || []).some(hasDebugPayload) ? (
            <div className="mt-4">
              <LlmRunTracePanel
                subSkills={run.sub_skills}
                executionTrace={run.execution_trace}
              />
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  )
}
