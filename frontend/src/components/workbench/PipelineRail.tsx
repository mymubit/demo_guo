import { CheckCircle2, Circle, Lock, AlertTriangle, Clock } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Badge } from '@/components/ui/Badge'
import { useWorkbenchDefinition } from '@/hooks/useWorkbenchDefinition'
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
  locked: 'text-ink-faint',
  pending: 'text-ink-muted',
  active: 'text-shell-accent',
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
        'group relative flex w-full items-start gap-2 rounded-md px-2 py-1.5 text-left transition',
        active ? 'bg-shell-accent/15' : 'hover:bg-canvas-muted',
        locked && 'cursor-not-allowed opacity-50 hover:bg-transparent',
        highlight && !locked && !active && 'bg-amber-50/80',
      )}
    >
      <span
        className={cn(
          'absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-shell-accent transition',
          active ? 'opacity-100' : 'opacity-0',
        )}
      />
      <Icon className={cn('mt-0.5 h-3.5 w-3.5 shrink-0', statusTone[status])} />
      <div className="min-w-0">
        <div className={cn('text-[13px] font-medium leading-tight text-ink', active && 'text-ink')}>
          {index != null ? `${index}. ` : ''}
          {stage.label_zh}
        </div>
        <div className="mt-0.5 truncate text-[10px] leading-tight text-ink-muted">
          {STATUS_LABEL_ZH[status]}
        </div>
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
  const { definition } = useWorkbenchDefinition()
  const ctx = {
    entry_type: settings.entry_type,
    enable_delivery: settings.creation_preferences.enable_delivery,
    creation_preferences: settings.creation_preferences,
  }
  const stages = mainPipelineStages(definition.stages, ctx)
  const qualityStages = qualityLoopStages(definition.stages, ctx)
  const qualityHighlight = isQualityPhaseHighlight(workflow)

  return (
    <aside className="flex h-full w-[clamp(11.5rem,14vw,13.5rem)] shrink-0 flex-col border-r border-border bg-surface">
      <div className="border-b border-border px-2.5 py-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-ink-faint">
          流水线
        </div>
        <div className="mt-0.5 text-[13px] font-semibold text-ink">创作主链</div>
        {workflow ? (
          <div className="mt-1.5">
            <Badge
              tone={
                workflow.status === 'blocked'
                  ? 'danger'
                  : workflow.status.startsWith('waiting')
                    ? 'warning'
                    : workflow.status === 'completed'
                      ? 'success'
                      : 'action'
              }
            >
              {WORKFLOW_STATUS_LABELS[workflow.status]}
            </Badge>
          </div>
        ) : null}
      </div>
      <ol className="flex-1 space-y-px overflow-auto p-1">
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
          <li className="pt-2">
            <div
              className={cn(
                'mb-0.5 px-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-ink-faint',
                qualityHighlight && 'text-amber-700',
              )}
            >
              质检环
            </div>
            <ul className="space-y-px">
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
