import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  FolderKanban,
  ArrowLeft,
  Clock,
  Calendar,
  Star,
  Sparkles,
  CheckCircle2,
  Loader2,
  FileText,
  RefreshCw,
  ArrowRight,
  Trash2,
  XCircle,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { works as worksApi } from '@/services/api'
import { getThemeMeta } from '@/constants/themeMeta'
import ThemeBadge from '@/components/ui/ThemeBadge'
import EmptyState from '@/components/ui/EmptyState'
import { Button } from '@/components/ui'
import { SectionEyebrow, PillFilterGroup, ConsumerListToolbar, ConsumerListToolbarSearch, ConsumerListToolbarActions, PageContainer } from '@/components/shared/ConsumerSection'
import { getWorkStatusMeta, WORK_FILTER_OPTIONS } from '@/utils/workStatus'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useWorksList } from '@/hooks/queries/useWorksList'

const STATUS_LIST = WORK_FILTER_OPTIONS
const FILTER_OPTIONS = STATUS_LIST.map((s) => ({ key: s.key, label: s.name }))

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
    <div className="relative min-h-screen py-12">
      <PageContainer width="7xl">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="mb-5 flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 bg-gray-50 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900"
            aria-label="返回首页"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <header className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="min-w-0">
              <SectionEyebrow>我的作品</SectionEyebrow>
              <h1 className="mt-3 text-3xl font-bold leading-tight tracking-tight text-gray-900 md:text-4xl">
                {pagination.total} 部剧本
                {generatingCount > 0 ? (
                  <span className="ml-2 text-lg font-medium text-brand-600/90 md:text-xl">
                    · {generatingCount} 部生成中
                  </span>
                ) : null}
              </h1>
              <p className="mt-2 text-sm text-gray-500 md:text-base">
                共 {pagination.total} 个项目 · 当前页已完成 {completedCount} 个 · 自动加密存档
              </p>
            </div>
            <PillFilterGroup
              className="shrink-0"
              options={FILTER_OPTIONS}
              value={statusFilter}
              onChange={(key) => {
                setStatusFilter(key)
                setPage(1)
              }}
            />
          </header>
        </motion.div>

        {/* 搜索与操作 */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="mb-8"
        >
          <ConsumerListToolbar>
            <ConsumerListToolbarSearch
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
              placeholder="搜索标题或创意描述…"
            />

            <ConsumerListToolbarActions>
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value)
                  setPage(1)
                }}
                className="sf-control h-11 w-[7.5rem] shrink-0 cursor-pointer whitespace-nowrap px-3 text-sm sm:w-32"
                aria-label="排序方式"
              >
                <option value="newest">最新创建</option>
                <option value="score">评分最高</option>
                <option value="episodes">集数最多</option>
              </select>

              <Button
                type="button"
                variant="ghost"
                size="md"
                iconLeft={RefreshCw}
                isLoading={loading}
                onClick={() => refetch()}
              >
                刷新
              </Button>

              <Button
                type="button"
                variant="gold"
                size="md"
                iconLeft={Sparkles}
                onClick={() => navigate('/drama')}
              >
                新建创作
              </Button>
            </ConsumerListToolbarActions>
          </ConsumerListToolbar>
        </motion.div>

        {loadError && (
          <div className="mb-6 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
            {loadError}
          </div>
        )}

        {/* 作品列表 / 空状态 */}
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
              className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-2 text-gray-600 transition-colors hover:bg-gray-100 disabled:opacity-40"
            >
              上一页
            </button>
            <span className="text-sm text-gray-500">
              第 {page} / {pagination.total_pages} 页 · 共 {pagination.total} 个作品
            </span>
            <button
              disabled={page >= pagination.total_pages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-2 text-gray-600 transition-colors hover:bg-gray-100 disabled:opacity-40"
            >
              下一页
            </button>
          </div>
        )}
      </PageContainer>
    </div>
  )
}

// ============ 作品卡片 ============
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

  const coverUrl = work.cover_url || work.cover
  const coverStyle = coverUrl
    ? { backgroundImage: `url(${coverUrl})` }
    : {
        background: `linear-gradient(135deg, ${theme.color}44 0%, ${theme.color}88 45%, rgba(15, 23, 42, 0.95) 100%)`,
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
      className="group cursor-pointer overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-all hover:border-brand-200 hover:shadow-md"
    >
      <div className="relative aspect-video w-full bg-cover bg-center" style={coverStyle} role="img" aria-label={work.title}>
        <div className="absolute inset-0 bg-gradient-to-t from-gray-900/70 via-transparent to-transparent" />
        <div className="absolute left-3 top-3">
          <ThemeBadge theme={theme} size="sm" />
        </div>
        <div className="absolute right-3 top-3 flex items-center gap-1.5">
          <div
            className="flex items-center gap-1.5 rounded-xl px-2.5 py-1 backdrop-blur-sm"
            style={{ background: meta.bg, color: meta.color }}
          >
            {meta.spin ? (
              <StatusIcon className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <StatusIcon className="h-3.5 w-3.5" />
            )}
            <span className="text-xs font-medium">{meta.label}</span>
          </div>
          <button
            type="button"
            title={work.raw_status === 'running' ? '创作中不可删除' : '删除作品'}
            disabled={deleting}
            onClick={(e) => {
              e.stopPropagation()
              onDelete?.(work)
            }}
            className="rounded-xl border border-transparent bg-gray-50 p-2 text-gray-500 transition-all transition-all hover:border-red-500/20 hover:bg-red-500/10 hover:text-red-400 disabled:opacity-50"
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          </button>
        </div>
      </div>

      <div className="p-4 pb-5">
        <h3 className="mb-1 line-clamp-2 text-base font-semibold text-gray-900 transition-colors group-hover:text-brand-600">
          {work.title}
        </h3>
        <p className="mb-2 line-clamp-2 text-xs text-gray-500">
          {work.idea ? (
            work.idea
          ) : (
            <span className="italic text-gray-400">
              {meta.key === 'draft' ? '尚未填写创意描述' : '暂无创意摘要'}
            </span>
          )}
        </p>
        <div className="text-xs text-gray-500">
          {theme.name} · {work.episodes} 集 · {work.format}
          {work.score ? (
            <span className="ml-2 inline-flex items-center gap-1 text-brand-600">
              <Star className="h-3 w-3 fill-brand-500" />
              {work.score}
            </span>
          ) : null}
        </div>

        {meta.progress > 0 && meta.progress < 100 && meta.key === 'generating' ? (
          <div className="mt-3">
            <div className="mb-1 flex justify-between text-[10px] text-gray-400">
              <span>创作进度</span>
              <span>{meta.progress}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full rounded-full bg-gradient-to-r from-gold-500 to-amber-400 transition-all"
                style={{ width: `${meta.progress}%` }}
              />
            </div>
          </div>
        ) : null}

        <div className="mt-3 flex items-center justify-between border-t border-gray-200 pt-3">
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            <Calendar className="h-3.5 w-3.5" />
            <span>{work.createdAt}</span>
          </div>
          <div className="flex items-center gap-1 text-sm text-brand-600 transition-all group-hover:gap-2">
            <span>{meta.cta}</span>
            <ArrowRight className="h-4 w-4" />
          </div>
        </div>
      </div>
    </motion.article>
  )
}

// ============ 加载骨架屏 ============
function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.05 }}
          className="overflow-hidden rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm"
        >
          <div className="aspect-video animate-pulse bg-gray-100" />
          <div className="space-y-3 p-4 pb-5">
            <div className="h-5 w-4/5 animate-pulse rounded-lg bg-gray-100" />
            <div className="h-3 w-full animate-pulse rounded bg-gray-50" />
            <div className="h-3 w-2/3 animate-pulse rounded bg-gray-50" />
          </div>
        </motion.div>
      ))}
    </div>
  )
}

// ============ 空状态 ============
function WorksEmptyState({ onNew, onClear, hasFilter }) {
  return (
    <EmptyState
      icon={FolderKanban}
      title={hasFilter ? '没有找到匹配的作品' : '暂无作品'}
      description={
        hasFilter
          ? '试试调整搜索关键词或筛选条件，看看其他作品吧'
          : '从一句话创意开始，让 AI 帮你生成完整的短剧剧本'
      }
      action={
        <button
          type="button"
          onClick={hasFilter ? onClear : onNew}
          className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl font-semibold btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all"
        >
          <Sparkles className="w-5 h-5" />
          {hasFilter ? '清除筛选' : '开始第一次创作'}
          <ArrowRight className="w-5 h-5" />
        </button>
      }
    />
  )
}
