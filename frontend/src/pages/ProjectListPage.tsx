import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Clapperboard, Plus, Settings2 } from 'lucide-react'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { PageShell } from '@/components/layout/PageShell'
import {
  formatRelativeTime,
  listRecentProjects,
  sortProjectsByRecent,
  syncRecentProjectsWithList,
  type RecentProjectRef,
} from '@/utils/recentProjects'
import type { DramaProjectSummary } from '@/types/domain'

const STATUS_LABEL: Record<string, string> = {
  active: '进行中',
  archived: '已归档',
  completed: '已完成',
  draft: '草稿',
}

function entryLabel(entryType?: string): string {
  return entryType === 'story_adapt' ? '改编' : '原创'
}

export function ProjectListPage() {
  const query = useQuery({
    queryKey: ['projects'],
    queryFn: () => dramaApi.listProjects(),
  })
  const [recent, setRecent] = useState<RecentProjectRef[]>(() => listRecentProjects().slice(0, 3))

  useEffect(() => {
    if (!query.data) return
    setRecent(syncRecentProjectsWithList(query.data).slice(0, 3))
  }, [query.data])

  const projects = useMemo(() => {
    if (!query.data) return [] as DramaProjectSummary[]
    return sortProjectsByRecent(query.data, recent)
  }, [query.data, recent])

  const continueProject: DramaProjectSummary | null = useMemo(() => {
    if (projects.length === 0) return null
    if (recent[0]) {
      return projects.find((p) => p.id === recent[0].id) ?? projects[0]
    }
    return projects[0]
  }, [projects, recent])

  return (
    <PageShell
      title="项目"
      description="管理原创与改编短剧项目，从最近作品快速继续。"
      actions={
        <Link to="/projects/new">
          <Button variant="action" iconLeft={<Plus className="h-4 w-4" />}>
            新建项目
          </Button>
        </Link>
      }
    >
      {query.isLoading ? <LoadingBlock /> : null}
      {query.isError ? (
        <ErrorBanner message={formatApiError(query.error)} onRetry={() => void query.refetch()} />
      ) : null}

      {query.data && query.data.length === 0 ? (
        <EmptyState
          title="还没有创作项目"
          description="先写名称与灵感，再完善题材设定，即可进入工作台跑主链。"
          action={
            <div className="flex flex-wrap items-center justify-center gap-3">
              <Link to="/projects/new">
                <Button variant="action" iconLeft={<Plus className="h-4 w-4" />}>
                  新建第一部短剧
                </Button>
              </Link>
              <Link
                to="/admin/model"
                className="text-sm text-action underline-offset-2 hover:underline"
              >
                先配置模型 →
              </Link>
            </div>
          }
        />
      ) : null}

      {query.data && query.data.length > 0 && continueProject ? (
        <div className="space-y-12">
          <section className="sf-panel relative overflow-hidden p-8 sm:p-10">
            <div
              className="pointer-events-none absolute inset-0 opacity-70"
              style={{
                background:
                  'radial-gradient(ellipse 55% 80% at 0% 50%, rgba(15,39,68,0.06), transparent 60%)',
              }}
            />
            <div className="relative flex flex-wrap items-end justify-between gap-6">
              <div className="min-w-0 max-w-2xl">
                <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
                  继续创作
                </div>
                <h2 className="mt-3 truncate text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
                  {continueProject.title || '未命名项目'}
                </h2>
                <p className="mt-2 text-sm text-ink-muted">
                  {entryLabel(continueProject.entry_type)}通道
                  {continueProject.updated_at
                    ? ` · 更新于 ${formatRelativeTime(continueProject.updated_at)}`
                    : null}
                </p>
              </div>
              <div className="flex shrink-0 flex-wrap gap-2">
                <Link to={`/projects/${continueProject.id}/settings`}>
                  <Button variant="secondary">创作设定</Button>
                </Link>
                <Link to={`/projects/${continueProject.id}/workbench`}>
                  <Button variant="action" iconLeft={<ArrowRight className="h-4 w-4" />}>
                    进入工作台
                  </Button>
                </Link>
              </div>
            </div>
          </section>

          {recent.length > 1 ? (
            <section>
              <h2 className="mb-5 text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
                最近打开
              </h2>
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {recent.map((item) => (
                  <Link
                    key={item.id}
                    to={`/projects/${item.id}/workbench`}
                    className="sf-panel block p-5 transition hover:border-action/35"
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-canvas-muted">
                        <Clapperboard className="h-4 w-4 text-action" />
                      </div>
                      <div className="min-w-0">
                        <div className="truncate font-medium text-ink">{item.title}</div>
                        <div className="mt-1.5 text-xs text-ink-muted">
                          {entryLabel(item.entry_type)} · {formatRelativeTime(item.visited_at)}
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}

          <section>
            <h2 className="mb-5 text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
              全部项目
            </h2>
            <ul className="flex flex-col gap-4">
              {projects.map((project) => (
                <li
                  key={project.id}
                  className="sf-panel flex items-center justify-between gap-6 px-6 py-5 transition hover:border-action/30"
                >
                  <div className="min-w-0">
                    <Link
                      to={`/projects/${project.id}/workbench`}
                      className="text-base font-medium text-ink hover:text-action"
                    >
                      {project.title || '未命名项目'}
                    </Link>
                    <div className="mt-2.5 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
                      <Badge tone={project.entry_type === 'original_track' ? 'action' : 'default'}>
                        {entryLabel(project.entry_type)}
                      </Badge>
                      {project.status ? (
                        <Badge
                          tone={
                            project.status === 'completed'
                              ? 'success'
                              : project.status === 'active'
                                ? 'action'
                                : 'default'
                          }
                        >
                          {STATUS_LABEL[project.status] ?? project.status}
                        </Badge>
                      ) : null}
                      {project.episode_count ? <span>{project.episode_count} 集</span> : null}
                      {project.updated_at ? (
                        <span>更新于 {formatRelativeTime(project.updated_at)}</span>
                      ) : null}
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    <Link to={`/projects/${project.id}/settings`}>
                      <Button
                        variant="secondary"
                        size="sm"
                        iconLeft={<Settings2 className="h-3.5 w-3.5" />}
                      >
                        创作设定
                      </Button>
                    </Link>
                    <Link to={`/projects/${project.id}/workbench`}>
                      <Button variant="action" size="sm">
                        进入工作台
                      </Button>
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      ) : null}
    </PageShell>
  )
}
