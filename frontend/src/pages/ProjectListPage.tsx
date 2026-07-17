import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Clapperboard, Plus, Settings2 } from 'lucide-react'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
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
    <div className="mx-auto max-w-6xl px-8 py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink">项目</h1>
          <p className="mt-1 text-sm text-ink-muted">管理原创与改编短剧项目，从最近作品快速继续</p>
        </div>
        <Link to="/projects/new">
          <Button iconLeft={<Plus className="h-4 w-4" />}>新建创作</Button>
        </Link>
      </div>

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
                <Button iconLeft={<Plus className="h-4 w-4" />}>新建第一部短剧</Button>
              </Link>
              <Link
                to="/admin/model"
                className="text-sm text-navy-600 underline-offset-2 hover:underline"
              >
                先配置模型 →
              </Link>
            </div>
          }
        />
      ) : null}

      {query.data && query.data.length > 0 && continueProject ? (
        <div className="space-y-6">
          <section className="overflow-hidden rounded-xl border border-slate-200 shadow-panel">
            <div className="flex flex-wrap items-center justify-between gap-4 bg-gradient-to-r from-navy-900 to-navy-800 px-5 py-4 text-white">
              <div className="min-w-0">
                <div className="text-xs font-medium tracking-wide text-slate-300">继续创作</div>
                <div className="mt-1 truncate text-lg font-semibold">
                  {continueProject.title || '未命名项目'}
                </div>
                <div className="mt-1 text-xs text-slate-400">
                  {entryLabel(continueProject.entry_type)}通道
                  {continueProject.updated_at
                    ? ` · 更新于 ${formatRelativeTime(continueProject.updated_at)}`
                    : null}
                </div>
              </div>
              <div className="flex shrink-0 gap-2">
                <Link to={`/projects/${continueProject.id}/settings`}>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="border-white/20 bg-white/10 text-white hover:bg-white/15"
                  >
                    创作设定
                  </Button>
                </Link>
                <Link to={`/projects/${continueProject.id}/workbench`}>
                  <Button size="sm" iconLeft={<ArrowRight className="h-3.5 w-3.5" />}>
                    进入工作台
                  </Button>
                </Link>
              </div>
            </div>
          </section>

          {recent.length > 1 ? (
            <section>
              <h2 className="mb-3 text-sm font-semibold text-ink">最近打开</h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {recent.map((item) => (
                  <Link
                    key={item.id}
                    to={`/projects/${item.id}/workbench`}
                    className="sf-panel block p-4 transition hover:border-navy-300"
                  >
                    <div className="flex items-start gap-3">
                      <Clapperboard className="mt-0.5 h-4 w-4 shrink-0 text-navy-700" />
                      <div className="min-w-0">
                        <div className="truncate font-medium text-ink">{item.title}</div>
                        <div className="mt-1 text-xs text-ink-muted">
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
            <h2 className="mb-3 text-sm font-semibold text-ink">全部项目</h2>
            <ul className="divide-y divide-slate-200 overflow-hidden rounded-xl border border-slate-200 bg-white">
              {projects.map((project) => (
                <li
                  key={project.id}
                  className="flex items-center justify-between gap-4 px-5 py-4 hover:bg-slate-50"
                >
                  <div className="min-w-0">
                    <Link
                      to={`/projects/${project.id}/workbench`}
                      className="text-base font-medium text-ink hover:text-brand-600"
                    >
                      {project.title || '未命名项目'}
                    </Link>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
                      <Badge tone={project.entry_type === 'original_track' ? 'action' : 'gold'}>
                        {entryLabel(project.entry_type)}
                      </Badge>
                      {project.status ? (
                        <Badge tone="default">
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
                      <Button size="sm">进入工作台</Button>
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      ) : null}
    </div>
  )
}
