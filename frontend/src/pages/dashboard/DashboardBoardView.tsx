import { useMemo } from 'react'
import type { ProjectStage, ProjectSummary } from '@/types/v3/domain'
import { STAGE_LABEL } from '../projectLabels'
import { ProjectCard } from './ProjectCard'

const STAGE_ORDER: ProjectStage[] = [
  'topic',
  'blueprint',
  'episodes',
  'writing',
  'quality',
  'delivery',
]

export function DashboardBoardView({
  projects,
  onArchive,
  onDelete,
}: {
  projects: ProjectSummary[]
  onArchive: (project: ProjectSummary) => void
  onDelete: (project: ProjectSummary) => void
}) {
  const projectsByStage = useMemo(() => {
    const grouped = Object.fromEntries(
      STAGE_ORDER.map((stage) => [stage, [] as ProjectSummary[]]),
    ) as Record<ProjectStage, ProjectSummary[]>

    for (const project of projects) {
      grouped[project.stage]?.push(project)
    }

    return grouped
  }, [projects])

  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {STAGE_ORDER.map((stage) => {
        const stageProjects = projectsByStage[stage]
        return (
          <section
            key={stage}
            aria-label={STAGE_LABEL[stage]}
            className="flex w-72 shrink-0 flex-col gap-2"
          >
            <header className="sf-panel flex items-center justify-between px-3 py-2">
              <h2 className="text-sm font-semibold text-ink">{STAGE_LABEL[stage]}</h2>
              <span className="text-xs text-ink-faint">{stageProjects.length}</span>
            </header>
            <div className="flex min-h-[6rem] flex-col gap-2">
              {stageProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onArchive={onArchive}
                  onDelete={onDelete}
                />
              ))}
            </div>
          </section>
        )
      })}
    </div>
  )
}
