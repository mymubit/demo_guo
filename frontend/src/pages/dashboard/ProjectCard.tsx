import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import type { ProjectSummary } from '@/types/v3/domain'
import { ENTRY_LABEL, STAGE_LABEL } from '../projectLabels'
import { pathForStage } from '../projectStagePaths'

function formatUpdatedAt(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function ProjectCard({
  project,
  onArchive,
  onDelete,
}: {
  project: ProjectSummary
  onArchive: (project: ProjectSummary) => void
  onDelete: (project: ProjectSummary) => void
}) {
  const workbenchHref = pathForStage(project.id, project.stage)

  return (
    <div className="sf-panel flex flex-col p-4 transition hover:border-action/40 hover:shadow-sm">
      <Link to={workbenchHref} className="min-w-0 flex-1">
        <h2 className="truncate text-base font-semibold text-ink">{project.title}</h2>
        <p className="mt-2 text-sm text-ink-muted">
          {`${ENTRY_LABEL[project.entry_type]} · ${STAGE_LABEL[project.stage]}`}
          {project.archived_at ? ' · 已归档' : ''}
        </p>
        <p className="mt-1 text-xs text-action">继续：{STAGE_LABEL[project.stage]}</p>
        <p className="mt-3 text-xs text-ink-faint">更新于 {formatUpdatedAt(project.updated_at)}</p>
      </Link>
      <div className="mt-3 flex flex-wrap gap-2 border-t border-border pt-3">
        {!project.archived_at ? (
          <Button type="button" variant="ghost" size="sm" onClick={() => onArchive(project)}>
            归档
          </Button>
        ) : null}
        <Button type="button" variant="ghost" size="sm" onClick={() => onDelete(project)}>
          删除
        </Button>
      </div>
    </div>
  )
}
