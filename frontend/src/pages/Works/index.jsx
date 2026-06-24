import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  FolderKanban,
  Clock,
  Star,
  Sparkles,
  CheckCircle2,
  Loader2,
  FileText,
  RefreshCw,
  ArrowRight,
  Trash2,
  XCircle,
  Search,
  Plus,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { works as worksApi } from '@/services/api'
import { getThemeMeta } from '@/constants/themeMeta'
import EmptyState from '@/components/ui/EmptyState'
import { Button, Card, Badge } from '@/components/ui'
import PageShell from '@/components/layout/PageShell'
import { getWorkStatusMeta, WORK_FILTER_OPTIONS } from '@/utils/workStatus'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useWorksList } from '@/hooks/queries/useWorksList'

const STATUS_LIST = WORK_FILTER_OPTIONS

export default function Works() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortBy, setSortBy] = useState('newest')
  const [page, setPage] = useState(1)
  const [deletingId, setDeletingId] = useState(null)
  const debouncedSearch = useDebouncedValue(search, 400)

  const { data, isLoading, error, refetch, isFetching } = useWorksList({
    page,
    status: statusFilter,
    keyword: debouncedSearch,
    ordering: sortBy,
  })
  const works = data?.items ?? []
  const pagination = data?.pagination ?? { total: 0, total_pages: 1, page_size: 12, page: 1 }
  const loading = isLoading || isFetching
  const loadError = error?.message ?? ''

  const deleteMutation = useMutation({
    mutationFn: (projectId) => worksApi.remove(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['works'] })
      toast.success('作品已删除')
    },
    onError: (e) => toast.error(e.message || '删除失败'),
    onSettled: () => setDeletingId(null),
  })

  const filtered = works
  const clearFilters = () => {
    setSearch('')
    setStatusFilter('all')
    setSortBy('newest')
    setPage(1)
  }

  const getTheme = (key) => getThemeMeta(key)
  const completedCount = works.filter((w) => w.status === 'completed').length
  const generatingCount = works.filter((w) => w.status === 'generating').length
  const totalCount = pagination.total

  const handleDelete = async (work) => {
    const pid = work.project_id
    if (!pid || deletingId) return
    const title = work.title || '该作品'
    const running = work.raw_status === 'running'
    const msg = running
      ? `「${title}」正在创作中，无法删除。请等待完成或失败后再试。`
      : `确定永久删除「${title}」？\n\n将同时删除剧本、大纲、分享链接等全部数据，且无法恢复。`
    if (running) {
      toast.error(msg)
      return
    }
    if (!window.confirm(msg)) return
    setDeletingId(pid)
    deleteMutation.mutate(pid)
  }

  return (
    <PageShell
      title="我的作品"
      description={`共 ${totalCount} 个项目 · ${completedCount} 个已完成${generatingCount > 0 ? ` · ${generatingCount} 个生成中` : ''}`}
      backTo="/"
      maxWidth="xl"
      actions={
        <Button
          variant="gold"
          iconLeft={<Plus className="w-4 h-4" />}
          onClick={() => navigate('/drama')}
        >
          新建创作
        </Button>
      }
    >
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6">
        <Card variant="glass" padding="md">
          <div className="text-2xl sm:text-3xl font-bold text-white">{totalCount}</div>
          <div className="text-xs text-slate-400 mt-1">全部作品</div>
        </Card>
        <Card variant="glass" padding="md">
          <div className="text-2xl sm:text-3xl font-bold text-gold-400">{generatingCount}</div>
          <div className="text-xs text-slate-400 mt-1">创作中</div>
        </Card>
        <Card variant="glass" padding="md">
          <div className="text-2xl sm:text-3xl font-bold text-emerald-400">{completedCount}</div>
          <div className="text-xs text-slate-400 mt-1">已完成</div>
        </Card>
        <Card variant="glass" padding="md">
          <div className="text-2xl sm:text-3xl font-bold text-cyan-400">{Math.round(completedCount / Math.max(totalCount, 1) * 100)}%</div>
          <div className="text-xs text-slate-400 mt-1">完成率</div>
        </Card>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="搜索标题或创意描述..."
            className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-gold-500/50 focus:ring-2 focus:ring-gold-500/20 transition-all"
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex gap-1 bg-white/5 p-1 rounded-xl border border-white/10 overflow-x-auto scrollbar-thin">
            {STATUS_LIST.map((s) => (
              <button
                key={s.key}
                onClick={() => { setStatusFilter(s.key); setPage(1) }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-all ${
                  statusFilter === s.key
                    ? 'bg-gold-500 text-navy-950 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {s.name}
              </button>
            ))}
          </div>
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1) }}
            className="bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-gold-500/50"
          >
            <option value="newest" className="bg-navy-900">最新创建</option>
            <option value="score" className="bg-navy-900">评分最高</option>
            <option value="episodes" className="bg-navy-900">集数最多</option>
          </select>
          <Button
            variant="secondary"
            size="sm"
            iconLeft={<RefreshCw className="w-4 h-4" />}
            isLoading={loading}
            onClick={() => refetch()}
          >
            刷新
          </Button>
        </div>
      </div>

      {loadError && (
        <div className="mb-6 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          {loadError}
        </div>
      )}

      {loading ? (
        <LoadingSkeleton />
      ) : filtered.length === 0 ? (
        <WorksEmptyState
          onNew={() => navigate('/drama')}
          onClear={clearFilters}
          hasFilter={!!search || statusFilter !== 'all'}
        />
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
        >
          {filtered.map((work, idx) => (
            <WorkCard
              key={work.project_id}
              work={work}
              index={idx}
              theme={getTheme(work.theme)}
              navigate={navigate}
              onDelete={handleDelete}
              deleting={deletingId === work.project_id}
            />
          ))}
        </motion.div>
      )}

      {!loading && pagination.total_pages > 1 && (
        <div className="mt-10 flex items-center justify-center gap-3">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-slate-300 transition-colors hover:bg-white/10 disabled:opacity-40"
          >
            上一页
          </button>
          <span className="text-sm text-slate-400">
            第 {page} / {pagination.total_pages} 页 · 共 {pagination.total} 个作品
          </span>
          <button
            disabled={page >= pagination.total_pages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-slate-300 transition-colors hover:bg-white/10 disabled:opacity-40"
          >
            下一页
          </button>
        </div>
      )}
    </PageShell>
  )
}

function WorkCard({ work, index, theme, navigate, onDelete, deleting }) {
  const meta = getWorkStatusMeta(work.status, work)
  const StatusIcon =
    meta.key === 'completed'
      ? CheckCircle2
      : meta.key === 'generating'
        ? Loader2
        : meta.key === 'failed'
          ? XCircle
          : meta.key === 'awaiting'
            ? Clock
            : FileText

  const coverStyle = {
    background: `linear-gradient(135deg, ${theme.color}33 0%, ${theme.color}66 45%, rgba(10, 14, 26, 0.95) 100%)`,
  }

  const goToWork = () => {
    const pid = work.project_id
    if (work.status === 'completed') {
      navigate(`/works/${pid}`)
    } else if (work.drama_workspace_url) {
      navigate(work.drama_workspace_url)
    } else if (pid) {
      navigate(`/drama/workspace/${pid}`)
    }
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ y: -2 }}
      onClick={goToWork}
      className="group cursor-pointer overflow-hidden rounded-xl border border-white/10 bg-white/[0.03] backdrop-blur-sm transition-all hover:border-white/20 hover:bg-white/[0.06]"
    >
      <div className="relative aspect-video w-full" style={coverStyle} role="img" aria-label={work.title}>
        <div className="absolute inset-0 bg-gradient-to-t from-navy-950/80 via-transparent to-transparent" />
        <div className="absolute right-3 top-3 flex items-center gap-1.5">
          <Badge tone={meta.tone || 'default'} size="sm" className="backdrop-blur-sm">
            {meta.spin ? <StatusIcon className="h-3 w-3 mr-1 animate-spin" /> : <StatusIcon className="h-3 w-3 mr-1" />}
            {meta.label}
          </Badge>
          <button
            type="button"
            title={work.raw_status === 'running' ? '创作中不可删除' : '删除作品'}
            disabled={deleting}
            onClick={(e) => {
              e.stopPropagation()
              onDelete?.(work)
            }}
            className="rounded-xl border border-transparent bg-black/30 backdrop-blur-sm p-2 text-slate-400 transition-all hover:border-red-500/20 hover:bg-red-500/10 hover:text-red-400 disabled:opacity-50"
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          </button>
        </div>
      </div>

      <div className="p-5">
        <h3 className="mb-1.5 line-clamp-1 text-base font-semibold text-slate-100 transition-colors group-hover:text-gold-300">
          {work.title}
        </h3>
        <p className="mb-3 line-clamp-2 text-xs text-slate-400 min-h-[32px]">
          {work.idea ? (
            work.idea
          ) : (
            <span className="italic text-slate-500">
              {meta.key === 'draft' ? '尚未填写创意描述' : '暂无创意摘要'}
            </span>
          )}
        </p>
        <div className="flex items-center gap-2 text-xs text-slate-500 flex-wrap">
          <span className="px-2 py-0.5 rounded-md bg-white/5">{theme.name}</span>
          <span>·</span>
          <span>{work.episodes} 集</span>
          {work.score ? (
            <>
              <span>·</span>
              <span className="inline-flex items-center gap-1 text-gold-400 font-medium">
                <Star className="h-3 w-3 fill-gold-500" />
                {work.score}
              </span>
            </>
          ) : null}
        </div>

        {meta.progress > 0 && meta.progress < 100 && meta.key === 'generating' ? (
          <div className="mt-4">
            <div className="mb-1 flex justify-between text-[10px] text-slate-400">
              <span>创作进度</span>
              <span>{meta.progress}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
              <div
                className="h-full rounded-full bg-gradient-to-r from-gold-400 to-gold-500 transition-all shadow-gold"
                style={{ width: `${meta.progress}%` }}
              />
            </div>
          </div>
        ) : null}

        <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
          <span className="text-xs text-slate-500">{work.createdAt}</span>
          <span className="text-xs text-gold-400 flex items-center gap-1 group-hover:gap-2 transition-all font-medium">
            {meta.cta}
            <ArrowRight className="h-3.5 w-3.5" />
          </span>
        </div>
      </div>
    </motion.article>
  )
}

function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.05 }}
          className="overflow-hidden rounded-xl border border-white/10 bg-white/[0.03]"
        >
          <div className="aspect-video animate-pulse bg-white/5" />
          <div className="space-y-3 p-5">
            <div className="h-5 w-4/5 animate-pulse rounded-lg bg-white/5" />
            <div className="h-3 w-full animate-pulse rounded bg-white/5" />
            <div className="h-3 w-2/3 animate-pulse rounded bg-white/5" />
          </div>
        </motion.div>
      ))}
    </div>
  )
}

function WorksEmptyState({ onNew, onClear, hasFilter }) {
  return (
    <EmptyState
      icon={<FolderKanban className="w-12 h-12 text-gold-400" />}
      title={hasFilter ? '没有找到匹配的作品' : '暂无作品'}
      description={
        hasFilter
          ? '试试调整搜索关键词或筛选条件，看看其他作品吧'
          : '从一句话创意开始，让 AI 帮你生成完整的短剧剧本'
      }
      actionLabel={hasFilter ? '清除筛选' : '开始第一次创作'}
      onAction={hasFilter ? onClear : onNew}
    />
  )
}
