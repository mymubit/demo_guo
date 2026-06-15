import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FolderKanban,
  Search,
  Filter,
  ArrowLeft,
  Film,
  Clock,
  Calendar,
  Star,
  Sparkles,
  CheckCircle2,
  Loader2,
  FileText,
  ChevronDown,
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
  const [showStatusMenu, setShowStatusMenu] = useState(false)
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
  const getStatus = (key) => STATUS_LIST.find((s) => s.key === key) || STATUS_LIST[0]

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
      <div className="particles-bg" />
      <div className="max-w-7xl mx-auto px-6 relative z-10">
        {/* 顶部标题 */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => navigate('/')}
              className="w-10 h-10 rounded-xl flex items-center justify-center bg-navy-800/50 hover:bg-navy-700/50 text-navy-200 hover:text-white transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="inline-flex items-center gap-2 badge">
              <FolderKanban className="w-4 h-4" />
              <span>我的作品库</span>
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-3">
            我的<span className="gradient-text">作品</span>
          </h1>
          <p className="text-lg text-navy-300">
            共 <span className="text-gold-400 font-semibold">{pagination.total}</span> 个项目 · 当前页已完成{' '}
            <span className="text-green-400 font-semibold">
              {works.filter((w) => w.status === 'completed').length}
            </span>{' '}
            个
          </p>
        </motion.div>

        {/* 搜索 + 筛选栏 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-2xl p-5 mb-8"
        >
          <div className="flex flex-col md:flex-row gap-3">
            {/* 搜索框 */}
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
              <input
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(1)
                }}
                placeholder="搜索作品标题或创意描述..."
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-navy-800/50 border border-navy-600/30 text-white placeholder-navy-500 focus:border-gold-400/50 focus:ring-2 focus:ring-gold-400/20 outline-none transition-all"
              />
            </div>

            {/* 状态筛选 */}
            <div className="relative">
              <button
                onClick={() => setShowStatusMenu(!showStatusMenu)}
                className="w-full md:w-auto px-5 py-3 rounded-xl bg-navy-800/50 hover:bg-navy-700/50 border border-navy-600/30 text-white flex items-center gap-2 transition-all"
              >
                <Filter className="w-4 h-4 text-gold-400" />
                <span className="text-sm">{getStatus(statusFilter).name}</span>
                <ChevronDown className="w-4 h-4 text-navy-300" />
              </button>
              <AnimatePresence>
                {showStatusMenu && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 top-full mt-2 w-44 py-2 rounded-2xl glass-card shadow-xl z-20"
                  >
                    {STATUS_LIST.map((s) => (
                      <button
                        key={s.key}
                        onClick={() => {
                          setStatusFilter(s.key)
                          setPage(1)
                          setShowStatusMenu(false)
                        }}
                        className={`w-full px-4 py-2.5 flex items-center gap-3 text-left transition-all ${
                          statusFilter === s.key
                            ? 'bg-gold-400/10 text-gold-400'
                            : 'text-navy-100 hover:bg-navy-700/30'
                        }`}
                      >
                        <span
                          className="w-2 h-2 rounded-full flex-shrink-0"
                          style={{ background: s.color }}
                        />
                        <span className="text-sm">{s.name}</span>
                        <span className="ml-auto text-xs text-navy-400">
                          {s.key === 'all'
                            ? works.length
                            : works.filter((w) => w.status === s.key).length}
                        </span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* 排序 */}
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value)
                setPage(1)
              }}
              className="px-5 py-3 rounded-xl bg-navy-800/50 hover:bg-navy-700/50 border border-navy-600/30 text-white outline-none transition-all cursor-pointer text-sm"
            >
              <option value="newest">最新创建</option>
              <option value="score">评分最高</option>
              <option value="episodes">集数最多</option>
            </select>

            {/* 刷新 */}
            <button
              onClick={() => refetch()}
              disabled={loading}
              className="px-5 py-3 rounded-xl bg-navy-800/50 hover:bg-navy-700/50 border border-navy-600/30 text-white flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </button>

            {/* 新建按钮 */}
            <button
              onClick={() => navigate('/creation')}
              className="px-5 py-3 rounded-xl font-semibold flex items-center gap-2 btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all"
            >
              <Sparkles className="w-4 h-4" />
              新建创作
            </button>
          </div>
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
            onNew={() => navigate('/creation')}
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
              className="px-4 py-2 rounded-xl bg-navy-800/50 border border-navy-600/30 text-navy-200 disabled:opacity-40"
            >
              上一页
            </button>
            <span className="text-sm text-navy-300">
              第 {page} / {pagination.total_pages} 页 · 共 {pagination.total} 个作品
            </span>
            <button
              disabled={page >= pagination.total_pages}
              onClick={() => setPage((p) => p + 1)}
              className="px-4 py-2 rounded-xl bg-navy-800/50 border border-navy-600/30 text-navy-200 disabled:opacity-40"
            >
              下一页
            </button>
          </div>
        )}
      </div>
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

  const goToWork = () => {
    const pid = work.project_id
    if (work.status === 'completed') {
      navigate(`/works/${pid}`)
    } else if (pid) {
      navigate(`/creation?project=${pid}`)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ y: -6, scale: 1.01 }}
      onClick={goToWork}
      className="glass-card rounded-3xl p-6 cursor-pointer group relative overflow-hidden transition-all hover:shadow-lg hover:shadow-gold-500/10 border border-navy-600/20"
    >
      {/* 装饰渐变 */}
      <div
        className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-20 blur-3xl group-hover:opacity-30 transition-opacity"
        style={{ background: theme.color, transform: 'translate(50%, -50%)' }}
      />

      <div className="relative">
        {/* 顶部：题材 + 状态 */}
        <div className="flex items-start justify-between mb-4">
          <ThemeBadge theme={theme} size="sm" />
          <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-1.5">
              <div
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl"
                style={{ background: meta.bg, color: meta.color }}
              >
                {meta.spin ? (
                  <StatusIcon className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <StatusIcon className="w-3.5 h-3.5" />
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
                className="p-2 rounded-xl text-navy-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all disabled:opacity-50"
              >
                {deleting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
              </button>
            </div>
            {meta.hint ? (
              <p className="text-[10px] text-navy-500 text-right max-w-[140px] leading-snug">{meta.hint}</p>
            ) : null}
          </div>
        </div>

        {/* 标题 */}
        <h3 className="text-xl font-bold text-white mb-3 group-hover:text-gold-400 transition-colors line-clamp-2">
          {work.title}
        </h3>

        {/* 创意摘要 */}
        <p className="text-sm text-navy-300 leading-relaxed mb-4 line-clamp-3 min-h-[3.75rem]">
          {work.idea ? (
            work.idea
          ) : (
            <span className="text-navy-500 italic">
              {meta.key === 'draft' ? '尚未填写创意描述，点击进入工作台补充' : '暂无创意摘要'}
            </span>
          )}
        </p>

        {meta.progress > 0 && meta.progress < 100 && meta.key === 'generating' ? (
          <div className="mb-4">
            <div className="flex justify-between text-[10px] text-navy-500 mb-1">
              <span>创作进度</span>
              <span>{meta.progress}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-navy-800/80 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-gold-500 to-amber-400 transition-all"
                style={{ width: `${meta.progress}%` }}
              />
            </div>
          </div>
        ) : null}

        {/* 元信息 */}
        <div className="flex flex-wrap gap-3 mb-5 text-xs text-navy-400">
          <div className="flex items-center gap-1.5">
            <Film className="w-3.5 h-3.5 text-navy-400" />
            <span>{work.episodes} 集</span>
          </div>
          <div className="flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-navy-400" />
            <span>{work.format}</span>
          </div>
          {work.score && (
            <div className="flex items-center gap-1.5">
              <Star className="w-3.5 h-3.5 text-gold-400 fill-gold-400" />
              <span className="text-gold-400 font-semibold">{work.score}</span>
            </div>
          )}
        </div>

        {/* 底部：时间 + 箭头 */}
        <div className="flex items-center justify-between pt-4 border-t border-navy-700/40">
          <div className="flex items-center gap-1.5 text-xs text-navy-400">
            <Calendar className="w-3.5 h-3.5" />
            <span>{work.createdAt}</span>
          </div>
          <div className="flex items-center gap-1 text-sm text-gold-400 group-hover:gap-2 transition-all">
            <span>{meta.cta}</span>
            <ArrowRight className="w-4 h-4" />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// ============ 加载骨架屏 ============
function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {Array.from({ length: 6 }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.05 }}
          className="glass-card rounded-3xl p-6 border border-navy-600/20 overflow-hidden"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="h-7 w-24 rounded-xl bg-navy-700/40 animate-pulse" />
            <div className="h-7 w-16 rounded-xl bg-navy-700/40 animate-pulse" />
          </div>
          <div className="h-6 w-4/5 rounded-lg bg-navy-700/40 animate-pulse mb-3" />
          <div className="h-4 w-full rounded bg-navy-700/30 animate-pulse mb-2" />
          <div className="h-4 w-5/6 rounded bg-navy-700/30 animate-pulse mb-2" />
          <div className="h-4 w-3/4 rounded bg-navy-700/30 animate-pulse mb-5" />
          <div className="flex gap-4 mb-5">
            <div className="h-4 w-16 rounded bg-navy-700/30 animate-pulse" />
            <div className="h-4 w-20 rounded bg-navy-700/30 animate-pulse" />
            <div className="h-4 w-12 rounded bg-navy-700/30 animate-pulse" />
          </div>
          <div className="flex justify-between pt-4 border-t border-navy-700/40">
            <div className="h-3 w-24 rounded bg-navy-700/30 animate-pulse" />
            <div className="h-4 w-16 rounded bg-navy-700/30 animate-pulse" />
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
