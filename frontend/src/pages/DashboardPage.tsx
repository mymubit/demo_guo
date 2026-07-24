import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LayoutGrid, List, Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { DailyCostAlertBanner } from '@/components/DailyCostAlertBanner'
import { FilterEmptyState } from '@/components/layout/FilterEmptyState'
import { ListPageToolbar } from '@/components/layout/ListPageToolbar'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { formatApiError } from '@/services/errors'
import { archiveProject, createProject, deleteProject, listProjects } from '@/services/v3/projects'
import type { ProjectSummary } from '@/types/v3/domain'
import { ArchiveConfirmDialog } from './ArchiveConfirmDialog'
import { DeleteConfirmDialog } from './DeleteConfirmDialog'
import { CreateProjectDialog } from './dashboard/CreateProjectDialog'
import { DashboardBoardView } from './dashboard/DashboardBoardView'
import { filterProjectsByTitle } from './dashboard/filterProjectsByTitle'
import { ProjectCard } from './dashboard/ProjectCard'

const PROJECTS_QUERY_KEY = ['v3', 'projects'] as const

type DashboardViewMode = 'list' | 'board'

export function DashboardPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [createOpen, setCreateOpen] = useState(false)
  const [includeArchived, setIncludeArchived] = useState(false)
  const [archiveTarget, setArchiveTarget] = useState<ProjectSummary | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ProjectSummary | null>(null)
  const [viewMode, setViewMode] = useState<DashboardViewMode>('list')
  const [searchQuery, setSearchQuery] = useState('')

  const projectsQuery = useQuery({
    queryKey: [...PROJECTS_QUERY_KEY, { includeArchived }],
    queryFn: () => (includeArchived ? listProjects(true) : listProjects()),
  })

  const filteredProjects = useMemo(
    () => filterProjectsByTitle(projectsQuery.data ?? [], searchQuery),
    [projectsQuery.data, searchQuery],
  )

  const createMutation = useMutation({
    mutationFn: (body: Parameters<typeof createProject>[0]) => createProject(body),
    onSuccess: (project) => {
      void queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY })
      setCreateOpen(false)
      navigate(`/projects/${project.id}/topic`)
    },
  })

  const archiveMutation = useMutation({
    mutationFn: (projectId: string) => archiveProject(projectId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY })
      setArchiveTarget(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (projectId: string) => deleteProject(projectId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY })
      setDeleteTarget(null)
    },
  })

  const handleArchive = (project: ProjectSummary) => {
    archiveMutation.reset()
    setArchiveTarget(project)
  }

  const handleDelete = (project: ProjectSummary) => {
    deleteMutation.reset()
    setDeleteTarget(project)
  }

  const actions = (
    <>
      <label className="inline-flex items-center gap-2 text-sm text-ink-muted">
        <input
          type="checkbox"
          checked={includeArchived}
          onChange={(event) => setIncludeArchived(event.target.checked)}
          className="h-4 w-4 rounded border-border"
        />
        显示已归档
      </label>
      <Button iconLeft={<Plus className="h-4 w-4" />} onClick={() => setCreateOpen(true)}>
        新建项目
      </Button>
    </>
  )

  const viewToggle = (
    <div className="inline-flex rounded-lg border border-border p-0.5" role="group" aria-label="视图切换">
      <Button
        type="button"
        size="sm"
        variant={viewMode === 'list' ? 'secondary' : 'ghost'}
        iconLeft={<List className="h-3.5 w-3.5" />}
        aria-pressed={viewMode === 'list'}
        onClick={() => setViewMode('list')}
      >
        列表
      </Button>
      <Button
        type="button"
        size="sm"
        variant={viewMode === 'board' ? 'secondary' : 'ghost'}
        iconLeft={<LayoutGrid className="h-3.5 w-3.5" />}
        aria-pressed={viewMode === 'board'}
        onClick={() => setViewMode('board')}
      >
        看板
      </Button>
    </div>
  )

  const hasProjects = projectsQuery.isSuccess && projectsQuery.data.length > 0
  const hasFilteredResults = filteredProjects.length > 0

  return (
    <PageShell title="创作仪表盘" description="管理你的短剧项目与创作进度。" actions={actions}>
      <div className="mb-4">
        <DailyCostAlertBanner />
      </div>

      {projectsQuery.isLoading ? (
        <p className="text-sm text-ink-muted">正在加载项目…</p>
      ) : null}

      {projectsQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(projectsQuery.error)}</p>
      ) : null}

      {projectsQuery.isSuccess && projectsQuery.data.length === 0 ? (
        <FilterEmptyState
          title="还没有项目"
          description="点击右上角「新建项目」，开始选题定调与后续创作。"
          variant="inbox"
        />
      ) : null}

      {hasProjects ? (
        <ListPageToolbar
          className="mb-4"
          search={searchQuery}
          onSearchChange={setSearchQuery}
          searchPlaceholder="搜索项目标题"
          count={filteredProjects.length}
          countLabel="个项目"
          actions={viewToggle}
        />
      ) : null}

      {hasProjects && !hasFilteredResults ? (
        <FilterEmptyState
          title="没有匹配的项目"
          description="试试其他关键词，或清除搜索条件。"
          variant="filter"
          onClearFilters={() => setSearchQuery('')}
        />
      ) : null}

      {hasProjects && hasFilteredResults && viewMode === 'list' ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onArchive={handleArchive}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : null}

      {hasProjects && hasFilteredResults && viewMode === 'board' ? (
        <DashboardBoardView
          projects={filteredProjects}
          onArchive={handleArchive}
          onDelete={handleDelete}
        />
      ) : null}

      <CreateProjectDialog
        open={createOpen}
        busy={createMutation.isPending}
        errorMessage={createMutation.isError ? formatApiError(createMutation.error) : null}
        onOpenChange={(open) => {
          setCreateOpen(open)
          if (!open) createMutation.reset()
        }}
        onSubmit={(body) => createMutation.mutate(body)}
      />

      <ArchiveConfirmDialog
        open={Boolean(archiveTarget)}
        busy={archiveMutation.isPending}
        projectTitle={archiveTarget?.title}
        errorMessage={archiveMutation.isError ? formatApiError(archiveMutation.error) : null}
        onOpenChange={(open) => {
          if (!open) {
            setArchiveTarget(null)
            archiveMutation.reset()
          }
        }}
        onConfirm={() => {
          if (archiveTarget) archiveMutation.mutate(archiveTarget.id)
        }}
      />

      <DeleteConfirmDialog
        open={Boolean(deleteTarget)}
        busy={deleteMutation.isPending}
        projectTitle={deleteTarget?.title}
        errorMessage={deleteMutation.isError ? formatApiError(deleteMutation.error) : null}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteTarget(null)
            deleteMutation.reset()
          }
        }}
        onConfirm={() => {
          if (deleteTarget) deleteMutation.mutate(deleteTarget.id)
        }}
      />
    </PageShell>
  )
}
