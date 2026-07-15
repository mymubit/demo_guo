import { CheckCircle2, Circle, Lock, AlertTriangle, Clock } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Badge } from '@/components/ui/Badge'
import {
  isQualityPhaseHighlight,
  mainPipelineStages,
  qualityLoopStages,
  resolveStageStatus,
  type StageRailStatus,
} from '@/utils/pipeline'
import type { ProjectSettings, WorkflowState } from '@/types/domain'
import type { StageDefinition } from '@/types/workbench'

const statusIcon: Record<StageRailStatus, typeof Circle> = {
  locked: Lock,
  pending: Circle,
  active: Clock,
  waiting: Clock,
  done: CheckCircle2,
  blocked: AlertTriangle,
}

const statusTone: Record<StageRailStatus, string> = {
  locked: 'text-slate-400',
  pending: 'text-slate-500',
  active: 'text-brand-600',
  waiting: 'text-amber-600',
  done: 'text-emerald-600',
  blocked: 'text-red-600',
}

const STATUS_LABEL_ZH: Record<StageRailStatus, string> = {
  locked: '已锁定',
  pending: '待开始',
  active: '进行中',
  waiting: '等待中',
  done: '已完成',
  blocked: '已阻塞',
}

const WORKFLOW_STATUS_LABELS: Record<WorkflowState['status'], string> = {
  active: '进行中',
  waiting_approval: '待审批',
  waiting_quality: '质检中',
  waiting_user: '待决策',
  completed: '已完成',
  blocked: '已阻塞',
}

function StageButton({
  stage,
  index,
  status,
  active,
  onSelect,
  highlight,
}: {
  stage: StageDefinition
  index?: number
  status: StageRailStatus
  active: boolean
  onSelect: (stage: StageDefinition) => void
  highlight?: boolean
}) {
  const Icon = statusIcon[status]
  const locked = status === 'locked'
  const label = `${index != null ? `${index}. ` : ''}${stage.label_zh}（${STATUS_LABEL_ZH[status]}）`

  return (
    <button
      type="button"
      disabled={locked}
      aria-disabled={locked}
      aria-current={active ? 'step' : undefined}
      aria-label={label}
      title={locked ? '该阶段尚未解锁' : undefined}
      onClick={() => {
        if (locked) return
        onSelect(stage)
      }}
      className={cn(
        'flex w-full items-start gap-2 rounded-lg px-3 py-2.5 text-left transition',
        active ? 'bg-brand-50 ring-1 ring-brand-200' : 'hover:bg-slate-50',
        locked && 'cursor-not-allowed opacity-50 hover:bg-transparent',
        highlight && !locked && 'ring-1 ring-amber-200 bg-amber-50/70',
      )}
    >
      <Icon className={cn('mt-0.5 h-4 w-4 shrink-0', statusTone[status])} />
      <div className="min-w-0">
        <div className="text-sm font-medium text-ink">
          {index != null ? `${index}. ` : ''}
          {stage.label_zh}
        </div>
        <div className="truncate text-xs text-ink-muted">{STATUS_LABEL_ZH[status]}</div>
      </div>
    </button>
  )
}

export function PipelineRail({
  settings,
  workflow,
  activeStageId,
  onSelect,
}: {
  settings: ProjectSettings
  workflow: WorkflowState | null
  activeStageId: string
  onSelect: (stage: StageDefinition) => void
}) {
  const ctx = {
    entry_type: settings.entry_type,
    enable_delivery: settings.creation_preferences.enable_delivery,
    creation_preferences: settings.creation_preferences,
  }
  const stages = mainPipelineStages(ctx)
  const qualityStages = qualityLoopStages(ctx)
  const qualityHighlight = isQualityPhaseHighlight(workflow)

  return (
    <aside className="flex h-full w-[clamp(12.5rem,16vw,15rem)] shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-3">
        <div className="text-xs font-medium uppercase tracking-wide text-ink-faint">流水线</div>
        <div className="mt-1 text-sm font-semibold text-ink">创作主链</div>
        {workflow ? (
          <div className="mt-2">
            <Badge
              tone={
                workflow.status === 'blocked'
                  ? 'danger'
                  : workflow.status.startsWith('waiting')
                    ? 'warning'
                    : workflow.status === 'completed'
                      ? 'success'
                      : 'brand'
              }
            >
              {WORKFLOW_STATUS_LABELS[workflow.status]}
            </Badge>
          </div>
        ) : null}
      </div>
      <ol className="flex-1 space-y-1 overflow-auto p-2">
        {stages.map((stage, index) => {
          const status = resolveStageStatus(stage, workflow)
          return (
            <li key={stage.id}>
              <StageButton
                stage={stage}
                index={index + 1}
                status={status}
                active={activeStageId === stage.id}
                onSelect={onSelect}
              />
            </li>
          )
        })}

        {qualityStages.length > 0 ? (
          <li className="pt-3">
            <div
              className={cn(
                'mb-1 px-3 text-[11px] font-semibold uppercase tracking-wide text-ink-faint',
                qualityHighlight && 'text-amber-700',
              )}
            >
              质检环
            </div>
            <ul className="space-y-1">
              {qualityStages.map((stage) => {
                const status = resolveStageStatus(stage, workflow)
                const highlight =
                  qualityHighlight &&
                  ((stage.id === 'revision' && workflow?.current_phase === 'revision') ||
                    (stage.id !== 'revision' &&
                      (workflow?.current_phase === 'quality' ||
                        workflow?.status === 'waiting_quality' ||
                        workflow?.status === 'waiting_user')))
                return (
                  <li key={stage.id}>
                    <StageButton
                      stage={stage}
                      status={status}
                      active={activeStageId === stage.id}
                      onSelect={onSelect}
                      highlight={highlight}
                    />
                  </li>
                )
              })}
            </ul>
          </li>
        ) : null}
      </ol>
    </aside>
  )
}
