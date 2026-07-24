import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Link,
  Navigate,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
  useParams,
} from 'react-router-dom'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { formatApiError } from '@/services/errors'
import { getProject } from '@/services/v3/projects'
import { cn } from '@/utils/cn'
import {
  adjacentStage,
  pathForStage,
  settingsPath,
  STAGE_PATH_ORDER,
  stageFromPathSegment,
  stageIndex,
  stageStepLabel,
} from './projectStagePaths'

export function ProjectWorkbenchLayout() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const navigate = useNavigate()

  const projectQuery = useQuery({
    queryKey: ['v3', 'project', id],
    queryFn: () => getProject(id!),
    enabled: Boolean(id),
  })

  const project = projectQuery.data
  const pathSegment = location.pathname.split('/').filter(Boolean)[2]
  const activeStage = stageFromPathSegment(pathSegment)
  const projectStageIndex = project ? stageIndex(project.stage) : -1

  const prev = activeStage ? adjacentStage(activeStage, -1) : null
  const next = activeStage ? adjacentStage(activeStage, 1) : null

  const title = project?.title ?? '项目工作台'

  const rail = useMemo(() => {
    if (!id) return null
    return (
      <nav className="space-y-1" aria-label="创作阶段">
        {STAGE_PATH_ORDER.map((stage, index) => {
          const to = pathForStage(id, stage)
          const reached = projectStageIndex < 0 || index <= projectStageIndex
          return (
            <NavLink
              key={stage}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition',
                  isActive
                    ? 'bg-action/10 font-semibold text-action'
                    : reached
                      ? 'text-ink hover:bg-canvas-muted'
                      : 'text-ink-faint hover:bg-canvas-muted/60',
                )
              }
            >
              <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full border border-border text-[11px]">
                {index + 1}
              </span>
              <span className="min-w-0 truncate">{stageStepLabel(stage)}</span>
            </NavLink>
          )
        })}
      </nav>
    )
  }, [id, projectStageIndex])

  if (!id) {
    return <p className="text-sm text-danger">缺少项目 ID</p>
  }

  if (projectQuery.isLoading) {
    return (
      <PageShell title="项目工作台" description="加载创作进度…">
        <p className="text-sm text-ink-muted">正在加载项目…</p>
      </PageShell>
    )
  }

  if (projectQuery.isError) {
    return (
      <PageShell title="项目工作台" description="无法加载项目">
        <p className="text-sm text-danger">{formatApiError(projectQuery.error)}</p>
        <Button
          type="button"
          variant="secondary"
          className="mt-3"
          onClick={() => navigate('/dashboard')}
        >
          返回仪表盘
        </Button>
      </PageShell>
    )
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col gap-4 lg:flex-row lg:gap-6">
      <aside className="w-full shrink-0 lg:w-52">
        <div className="sf-panel space-y-3 p-3">
          <div className="px-1">
            <p className="text-xs text-ink-faint">创作向导</p>
            <h1 className="mt-1 truncate text-sm font-semibold text-ink" title={title}>
              {title}
            </h1>
          </div>
          {rail}
          <Link
            to={settingsPath(id)}
            className="block rounded-md px-3 py-2 text-xs text-ink-muted underline-offset-2 hover:underline"
          >
            项目设置与回滚
          </Link>
        </div>
      </aside>

      <div className="min-w-0 flex-1 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm text-ink-muted">
            {activeStage ? stageStepLabel(activeStage) : '项目'}
            {project ? ` · 进度阶段：${stageStepLabel(project.stage)}` : ''}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant="secondary"
              disabled={!prev}
              onClick={() => prev && navigate(pathForStage(id, prev))}
            >
              上一步
            </Button>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              disabled={!next}
              onClick={() => next && navigate(pathForStage(id, next))}
            >
              下一步
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => navigate(settingsPath(id))}
            >
              设置
            </Button>
          </div>
        </div>
        <Outlet />
      </div>
    </div>
  )
}

/** index：按项目当前 stage 跳转子路径 */
export function ProjectStageRedirect() {
  const { id } = useParams<{ id: string }>()
  const projectQuery = useQuery({
    queryKey: ['v3', 'project', id],
    queryFn: () => getProject(id!),
    enabled: Boolean(id),
  })

  if (!id) return null
  if (projectQuery.isLoading) {
    return <p className="text-sm text-ink-muted">正在进入当前阶段…</p>
  }
  if (projectQuery.isError || !projectQuery.data) {
    return (
      <p className="text-sm text-danger">
        {projectQuery.isError ? formatApiError(projectQuery.error) : '项目不存在'}
      </p>
    )
  }

  return <Navigate to={pathForStage(id, projectQuery.data.stage)} replace />
}
