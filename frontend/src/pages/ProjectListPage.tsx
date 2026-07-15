import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'

export function ProjectListPage() {
  const query = useQuery({
    queryKey: ['projects'],
    queryFn: () => dramaApi.listProjects(),
  })

  return (
    <div className="mx-auto max-w-6xl px-8 py-8">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink">项目</h1>
          <p className="mt-1 text-sm text-ink-muted">管理原创与改编短剧项目</p>
        </div>
        <Link to="/projects/new">
          <Button iconLeft={<Plus className="h-4 w-4" />}>新建项目</Button>
        </Link>
      </div>

      {query.isLoading ? <LoadingBlock /> : null}
      {query.isError ? (
        <ErrorBanner message={formatApiError(query.error)} onRetry={() => void query.refetch()} />
      ) : null}

      {query.data && query.data.length === 0 ? (
        <EmptyState
          title="还没有项目"
          description="从原创通道或故事改编通道创建第一个项目"
          action={
            <Link to="/projects/new">
              <Button>新建项目</Button>
            </Link>
          }
        />
      ) : null}

      {query.data && query.data.length > 0 ? (
        <ul className="divide-y divide-slate-200 overflow-hidden rounded-xl border border-slate-200 bg-white">
          {query.data.map((project) => (
            <li key={project.id} className="flex items-center justify-between gap-4 px-5 py-4 hover:bg-slate-50">
              <div className="min-w-0">
                <Link to={`/projects/${project.id}/workbench`} className="text-base font-medium text-ink hover:text-brand-600">
                  {project.title || '未命名项目'}
                </Link>
                <div className="mt-1 flex items-center gap-2 text-xs text-ink-muted">
                  <Badge tone={project.entry_type === 'original_track' ? 'brand' : 'gold'}>
                    {project.entry_type === 'original_track' ? '原创' : '改编'}
                  </Badge>
                  {project.episode_count ? <span>{project.episode_count} 集</span> : null}
                  {project.updated_at ? <span>更新于 {new Date(project.updated_at).toLocaleString()}</span> : null}
                </div>
              </div>
              <div className="flex shrink-0 gap-2">
                <Link to={`/projects/${project.id}/settings`}>
                  <Button variant="secondary" size="sm">
                    设置
                  </Button>
                </Link>
                <Link to={`/projects/${project.id}/workbench`}>
                  <Button size="sm">进入工作台</Button>
                </Link>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
