import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { ErrorBanner } from '@/components/ui/Tabs'
import { USER_DECISION_OPTIONS } from '@/config/workbench'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { createCommandId } from '@/utils/cn'
import {
  complianceRiskTypeLabelZh,
  qualityDimensionLabelZh,
} from '@/utils/reportLabels'
import type { UserDecisionOption, WorkflowState } from '@/types/domain'

type QualityReportLite = {
  overall_score?: number
  grade?: string
  verdict?: string
  needs_revision?: boolean
  dimensions?: Record<string, { score?: number }>
}

type ComplianceReportLite = {
  overall_result?: string
  blocking_issues?: unknown[]
  risk_items?: Array<{ type: string; description: string; suggestion: string }>
}

export function QualityLoopPanel({
  projectId,
  workflow,
  qualityReport,
  complianceReport,
}: {
  projectId: string
  workflow: WorkflowState
  qualityReport?: QualityReportLite | null
  complianceReport?: ComplianceReportLite | null
}) {
  const qc = useQueryClient()
  const decisionMutation = useMutation({
    mutationFn: (option: UserDecisionOption) =>
      dramaApi.postWorkflowCommand(projectId, {
        command_id: createCommandId('quality'),
        event: option,
        expected_version: workflow.version,
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['workflow', projectId] })
    },
  })

  const waitingUser = workflow.status === 'waiting_user'
  const options =
    workflow.pending_user_options?.length
      ? USER_DECISION_OPTIONS.filter((o) => workflow.pending_user_options?.includes(o.value))
      : USER_DECISION_OPTIONS

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="sf-section-title">质检环</h3>
        <div className="text-xs text-ink-muted">修复轮次 · {workflow.revision_round}</div>
      </div>

      <div className="grid grid-cols-2 gap-5">
        <section className="sf-panel p-5">
          <h4 className="text-sm font-semibold text-ink">评分</h4>
          {qualityReport ? (
            <div className="mt-3 space-y-2 text-sm">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-semibold text-action">
                  {qualityReport.overall_score ?? '—'}
                </span>
                <span className="text-ink-muted">{qualityReport.grade}</span>
              </div>
              <p className="text-ink-muted">{qualityReport.verdict}</p>
              {qualityReport.dimensions ? (
                <ul className="mt-2 grid grid-cols-2 gap-1 text-xs text-ink-muted">
                  {Object.entries(qualityReport.dimensions).map(([k, v]) => (
                    <li key={k} className="flex justify-between rounded bg-canvas px-2 py-1">
                      <span>{qualityDimensionLabelZh(k)}</span>
                      <span>{v.score ?? '—'}</span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : (
            <p className="mt-3 text-sm text-ink-muted">暂无评分报告</p>
          )}
        </section>

        <section className="sf-panel p-5">
          <h4 className="text-sm font-semibold text-ink">合规</h4>
          {complianceReport ? (
            <div className="mt-3 space-y-2 text-sm">
              <p className="font-medium text-ink">{complianceReport.overall_result}</p>
              <p className="text-ink-muted">
                阻断问题：{complianceReport.blocking_issues?.length ?? 0}
              </p>
              <ul className="space-y-1">
                {(complianceReport.risk_items ?? []).slice(0, 6).map((item, idx) => (
                  <li key={`${item.type}-${idx}`} className="rounded bg-canvas px-2 py-1.5 text-xs">
                    <span className="font-medium text-amber-700">
                      {complianceRiskTypeLabelZh(item.type)}
                    </span>
                    <span className="ml-2 text-ink-muted">{item.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="mt-3 text-sm text-ink-muted">暂无合规报告</p>
          )}
        </section>
      </div>

      {workflow.score_history.length > 0 ? (
        <div className="text-xs text-ink-muted">
          分数历史：{workflow.score_history.map((s) => s.toFixed(1)).join(' → ')}
        </div>
      ) : null}

      {waitingUser ? (
        <section className="sf-panel border-amber-200 bg-amber-50/60 p-5">
          <h4 className="text-sm font-semibold text-amber-900">等待用户决策</h4>
          <p className="mt-1 text-sm text-amber-800">质检未自动通过，请三选一继续流程。</p>
          {decisionMutation.isError ? (
            <div className="mt-3">
              <ErrorBanner message={formatApiError(decisionMutation.error)} />
            </div>
          ) : null}
          <div className="mt-5 flex flex-wrap gap-2">
            {options.map((opt) => (
              <Button
                key={opt.value}
                variant={opt.value === 'accept_current' ? 'action' : 'secondary'}
                loading={decisionMutation.isPending}
                onClick={() => decisionMutation.mutate(opt.value)}
              >
                {opt.label}
              </Button>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}
