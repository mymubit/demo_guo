import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { CommandRunStatus, CommandRunSummary } from '@/types/v3/domain'

export const STAGE_RUN_STATUS_LABEL: Record<CommandRunStatus, string> = {
  queued: '排队中',
  running: '进行中',
  succeeded: '已完成',
  failed: '失败',
  unsupported: '暂不支持',
}

export function isStageRunInProgress(run: CommandRunSummary | null | undefined): boolean {
  if (!run) return false
  return run.status === 'queued' || run.status === 'running'
}

export type StagePrerequisite = {
  message: string
  to: string
  linkLabel: string
}

export type StageNextStep = {
  to: string
  label: string
  hint?: string
}

interface StageStatusPanelProps {
  /** 任务区标题，默认「最近任务」 */
  runTitle?: string
  run?: CommandRunSummary | null
  idleHint?: string
  /** 生成成功且尚未确认时的提示 */
  generateSucceededHint?: string
  prerequisite?: StagePrerequisite | null
  nextStep?: StageNextStep | null
  children?: ReactNode
}

export function StageStatusPanel({
  runTitle = '最近任务',
  run,
  idleHint,
  generateSucceededHint,
  prerequisite,
  nextStep,
  children,
}: StageStatusPanelProps) {
  const inProgress = isStageRunInProgress(run)

  return (
    <section className="sf-panel space-y-2 p-4" data-testid="stage-status-panel">
      {prerequisite ? (
        <p className="text-sm text-ink-muted">
          {prerequisite.message}
          <Link to={prerequisite.to} className="ml-2 text-action underline">
            {prerequisite.linkLabel}
          </Link>
        </p>
      ) : null}

      {children}

      {run ? (
        <div className="space-y-1 text-sm">
          <p className="text-ink-muted">
            {runTitle}：{STAGE_RUN_STATUS_LABEL[run.status] ?? run.status}
            {inProgress ? '（自动刷新中…）' : ''}
          </p>
          {run.status === 'failed' && run.error_message ? (
            <p className="text-danger">{run.error_message}</p>
          ) : null}
          {run.status === 'succeeded' && generateSucceededHint ? (
            <p className="text-ink-muted">{generateSucceededHint}</p>
          ) : null}
        </div>
      ) : idleHint && !prerequisite ? (
        <p className="text-sm text-ink-muted">{idleHint}</p>
      ) : null}

      {nextStep ? (
        <div
          className="rounded-md border border-action/30 bg-action/5 px-3 py-2 text-sm"
          data-testid="stage-next-step"
        >
          <p className="text-ink">
            {nextStep.hint ?? '本阶段已就绪，可进入下一阶段继续创作。'}
          </p>
          <Link
            to={nextStep.to}
            className="mt-1 inline-flex font-medium text-action underline-offset-2 hover:underline"
          >
            {nextStep.label}
          </Link>
        </div>
      ) : null}
    </section>
  )
}
