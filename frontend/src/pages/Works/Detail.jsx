import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Download,
  Share2,
  Copy,
  Check,
  Clock,
  FileText,
  Sparkles,
  Star,
  Users,
  ChevronRight,
} from 'lucide-react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { works as worksApi, creation } from '@/services/api'
import { formatDateTime } from '@/utils/date'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import ScoreReport from '@/components/creation/ScoreReport'
import GateReport from '@/components/creation/GateReport'
import WorkVisualizationSection from '@/components/works/WorkVisualizationSection'
import WorkMetaPanel from '@/components/works/WorkMetaPanel'
import { PageContainer } from '@/components/shared/ConsumerSection'
import { cn } from '@/utils/cn'

import { getThemeMeta } from '@/constants/themeMeta'
import ThemeBadge from '@/components/ui/ThemeBadge'
import { Button } from '@/components/ui'

import { getWorkStatusMeta } from '@/utils/workStatus'
import { useWorkDetail } from '@/hooks/queries/useWorkDetail'

function statusBadge(status, work = {}) {
  const meta = getWorkStatusMeta(status, work)
  const tone =
    meta.key === 'completed'
      ? 'bg-green-500/15 text-green-400'
      : meta.key === 'generating'
        ? 'bg-gold-500/15 text-brand-600'
        : meta.key === 'failed'
          ? 'bg-red-500/15 text-red-400'
          : meta.key === 'awaiting'
            ? 'bg-blue-500/15 text-blue-300'
            : 'bg-navy-400/15 text-gray-600'
  return { text: meta.label, cls: tone, hint: meta.hint }
}

export default function WorksDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: work, isLoading: loading, error, refetch } = useWorkDetail(id)
  const loadError = error?.message ?? ''
  const [copied, setCopied] = useState(false)
  const [shareOpen, setShareOpen] = useState(false)
  const [shareLink, setShareLink] = useState('')
  const [sharing, setSharing] = useState(false)
  const [downloading, setDownloading] = useState(null)
  const [polishApplying, setPolishApplying] = useState(false)
  const [selectedPolish, setSelectedPolish] = useState(() => new Set())

  const reloadWork = async () => {
    try {
      const result = await refetch()
      if (result.error) throw result.error
    } catch (err) {
      toast.error(err.message || '刷新失败')
    }
  }

  const handleCopy = () => {
    if (!work) return
    navigator.clipboard?.writeText(window.location.href)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = async (type) => {
    if (!work?.project_id) return
    setDownloading(type)
    try {
      if (type === 'md' || type === 'markdown') {
        const data = await worksApi.exportMarkdown(work.project_id)
        const blob = new Blob([data.content], { type: 'text/markdown;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = data.filename || `${work.title || 'script'}.md`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        return
      }
      const format = type === 'html' ? 'html' : type
      const blob = await creation.download(work.project_id, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${work.title || 'script'}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      toast.error(err.message || '下载失败')
    } finally {
      setTimeout(() => setDownloading(null), 800)
    }
  }

  const togglePolishIndex = (index) => {
    setSelectedPolish((prev) => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  const handleApplyPolish = async (applyAll = false) => {
    if (!work?.project_id) return
    setPolishApplying(true)
    try {
      await worksApi.applyPolish(work.project_id, {
        apply_all: applyAll,
        indices: applyAll ? undefined : Array.from(selectedPolish),
      })
      toast.success('润色建议已写入剧本备注')
      await reloadWork()
      setSelectedPolish(new Set())
    } catch (err) {
      toast.error(err.message || '应用失败')
    } finally {
      setPolishApplying(false)
    }
  }

  const handleShare = async () => {
    if (!work?.project_id) return
    setSharing(true)
    try {
      const res = await worksApi.share(work.project_id, {
        view_limit: 100,
        valid_days: 7,
        allow_download: false,
      })
      const link =
        res?.share_url ||
        `${window.location.origin}/share/${res?.share_token || ''}`
      setShareLink(link)
      setShareOpen(true)
    } catch (err) {
      toast.error(err.message || '生成分享链接失败')
    } finally {
      setSharing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen py-12 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 rounded-full border-4 border-gold-400 border-t-transparent"
        />
      </div>
    )
  }

  if (!work) {
    return (
      <div className="min-h-screen py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">作品不存在</h2>
          <p className="text-gray-500 mb-6">{loadError || '找不到该作品或您无权限访问'}</p>
          <button
            onClick={() => navigate('/works')}
            className="btn-gold inline-flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            返回作品列表
          </button>
        </div>
      </div>
    )
  }

  const theme = getThemeMeta(work.theme)
  const statusInfo = statusBadge(work.status, work)

  return (
    <div className="relative min-h-screen py-12">
      <PageContainer width="7xl" className="py-8 md:py-12">
        {/* 返回导航 */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <button
            onClick={() => navigate('/works')}
            className="inline-flex items-center gap-2 text-gray-500 hover:text-brand-600 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>返回作品列表</span>
          </button>
        </motion.div>

        {/* 封面 Hero + 标题操作 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8 overflow-hidden rounded-3xl border border-gray-200"
        >
          <div
            className="relative h-44 md:h-52 bg-cover bg-center"
            style={{
              backgroundImage: `linear-gradient(135deg, ${theme.color}55 0%, #0a1628 55%, #050d18 100%)`,
            }}
          >
            <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/70 to-transparent" />
          </div>
          <div className="flex flex-wrap items-end justify-between gap-4 bg-slate-950 px-6 pb-6 md:px-7">
            <div className="-mt-10 min-w-0 flex-1">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <ThemeBadge theme={theme} size="md" className="!px-3 !py-1.5" />
                {work.overall_score != null ? (
                  <div className="inline-flex items-center gap-1.5 rounded-full bg-gold-400/15 px-3 py-1 text-xs font-semibold text-brand-600">
                    <Star className="h-3.5 w-3.5 fill-brand-500" />
                    {work.overall_score} 分 · {work.grade || '—'}
                  </div>
                ) : (
                  <div className="inline-flex items-center gap-1.5 rounded-full bg-gold-400/15 px-3 py-1 text-xs font-semibold text-brand-600">
                    {work.progress_percent || 0}% 生成中
                  </div>
                )}
                <div className={cn('inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold', statusInfo.cls)}>
                  {statusInfo.text}
                </div>
                {(work.current_stage === 'ready' || work.drama?.delivery_status === 'ready') && (
                  <div className="inline-flex items-center rounded-full bg-green-500/15 px-3 py-1 text-xs font-semibold text-green-400">
                    可发布
                  </div>
                )}
              </div>
              <h1 className="text-3xl font-bold leading-tight text-gray-900 md:text-4xl">
                {work.title || '未命名剧本'}
              </h1>
              <p className="mt-2 text-sm text-gray-400">
                {theme.name} · {work.episode_count || 0} 集 · {work.format_variant || '通用'} ·{' '}
                {formatDateTime(work.created_at)}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {work.status !== 'completed' && work.project_id && (
                <button
                  onClick={() =>
                    navigate(work.drama_workspace_url || `/drama/workspace/${work.project_id}`)
                  }
                  className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold btn-gold"
                >
                  <Sparkles className="w-4 h-4" />
                  继续编辑
                </button>
              )}
              <button
                onClick={() => handleDownload('md')}
                disabled={work.status !== 'completed'}
                className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm font-medium text-gray-900 transition-all hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Download className="w-4 h-4" />
                Markdown
                {downloading === 'md' && <span className="text-xs">…</span>}
              </button>
              <button
                onClick={() => handleDownload('html')}
                disabled={work.status !== 'completed'}
                className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm font-medium text-gray-900 transition-all hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Download className="w-4 h-4" />
                HTML
                {downloading === 'html' && <span className="text-xs">…</span>}
              </button>
              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm font-medium text-gray-900 transition-all hover:bg-gray-100"
              >
                {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                {copied ? '已复制' : '复制链接'}
              </button>
              <button
                onClick={handleShare}
                disabled={work.status !== 'completed' || sharing}
                className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold btn-gold transition-all hover:shadow-lg hover:shadow-gold-500/30 disabled:opacity-50"
              >
                <Share2 className="w-4 h-4" />
                {sharing ? '生成中…' : '分享'}
              </button>
            </div>
          </div>
        </motion.div>

        {(work.status === 'completed' ||
          work.scoreReport ||
          work.gateSummary ||
          work.reviewReport ||
          work.marketingKit) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.11 }}
            className="rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-8 mb-8"
          >
            <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Users className="w-5 h-5 text-brand-600" />
                智能分析
              </h2>
            </div>

            {work.projectBrief?.workingTitle && (
              <div className="mb-6 rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-brand-600 mb-2">项目简报</h3>
                <p className="text-sm text-gray-600">
                  {work.projectBrief.workingTitle}
                  {work.projectBrief.episodeCount != null && ` · ${work.projectBrief.episodeCount} 集`}
                </p>
                {work.projectBrief.writingBrief && (
                  <p className="text-sm text-gray-500 mt-2 line-clamp-3">{work.projectBrief.writingBrief}</p>
                )}
              </div>
            )}

            {work.scoreReport?.overallScore != null && (
              <div className="mb-6 rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-brand-600 mb-2">深度评分</h3>
                <p className="text-sm text-gray-600">
                  综合 {work.scoreReport.overallScore ?? '—'} 分
                  {work.scoreReport.grade ? ` · ${work.scoreReport.grade} 级` : ''}
                </p>
              </div>
            )}

            {work.reviewReport && (
              <div className="mb-6 rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-brand-600 mb-2">质检报告</h3>
                <p className="text-sm text-gray-600 mb-2">
                  状态：{work.reviewReport.passed ? '通过' : '待优化'}
                  {work.reviewReport.pacingPassed === false && ' · 节奏需调整'}
                </p>
                {(work.reviewReport.issues || []).length > 0 && (
                  <ul className="space-y-1 text-sm text-gray-500">
                    {work.reviewReport.issues.map((issue, i) => (
                      <li key={i}>· {typeof issue === 'string' ? issue : issue.message || JSON.stringify(issue)}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {(work.polishLog?.suggestions || []).length > 0 && (
              <div className="mb-6 rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-5">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                  <h3 className="text-sm font-semibold text-brand-600">润色建议</h3>
                  {work.polishLog.applied && (
                    <span className="text-xs text-green-400">已应用部分建议</span>
                  )}
                </div>
                <ul className="space-y-2 mb-4">
                  {work.polishLog.suggestions.map((s) => (
                    <li
                      key={s.index ?? s.advice}
                      className="flex items-start gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm text-gray-600"
                    >
                      <input
                        type="checkbox"
                        checked={selectedPolish.has(s.index)}
                        onChange={() => togglePolishIndex(s.index)}
                        className="mt-1 rounded border-gray-300"
                      />
                      <div className="min-w-0 flex-1">
                        {s.episodeNumber != null && (
                          <span className="text-xs text-brand-600/90 mr-2">第{s.episodeNumber}集</span>
                        )}
                        {s.field && <span className="text-xs text-gray-400 mr-2">{s.field}</span>}
                        <p className="whitespace-pre-wrap">{s.advice}</p>
                      </div>
                    </li>
                  ))}
                </ul>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={polishApplying || selectedPolish.size === 0}
                    onClick={() => handleApplyPolish(false)}
                    className="px-4 py-2 rounded-xl text-sm font-medium btn-gold disabled:opacity-50"
                  >
                    {polishApplying ? '写入中…' : `应用选中（${selectedPolish.size}）`}
                  </button>
                  <button
                    type="button"
                    disabled={polishApplying}
                    onClick={() => handleApplyPolish(true)}
                    className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-2 text-sm font-medium text-gray-900 disabled:opacity-50"
                  >
                    全部应用
                  </button>
                </div>
              </div>
            )}

            {(work.marketingKit?.titles || []).length > 0 && (
              <div className="rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-brand-600 mb-3">宣发物料</h3>
                <div className="space-y-3">
                  <AgentList label="推荐标题" items={work.marketingKit.titles} />
                  <AgentList label="切片钩子" items={work.marketingKit.clipHooks} />
                  <AgentList label="海报 Slogan" items={work.marketingKit.posterSlogans} />
                </div>
              </div>
            )}

            {!work.scoreReport?.overallScore &&
              !work.reviewReport &&
              !(work.marketingKit?.titles || []).length &&
              !(work.polishLog?.suggestions || []).length && (
                <p className="text-sm text-gray-400">
                  暂无智能分析结果，请在创作工作台运行独立 Agent。
                </p>
              )}
          </motion.div>
        )}

        {work.gateSummary && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-8 mb-8"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-4">逐集质检</h2>
            <GateReport summary={work.gateSummary} />
          </motion.div>
        )}

        {work.scoreReport && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-8 mb-8"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8 维评分</h2>
            <ScoreReport report={work.scoreReport} />
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18 }}
        >
          <WorkVisualizationSection projectId={work.project_id} />
        </motion.div>

        {/* 剧本正文 — 左正文 / 右元信息 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8 grid grid-cols-1 gap-5 lg:grid-cols-[1fr_320px]"
        >
          <section className="rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-5 md:p-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 pb-4">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-brand-600" />
                <h2 className="text-xl font-bold text-gray-900">剧本内容</h2>
              </div>
              <span className="rounded-full border border-gold-400/40 bg-gold-400/10 px-3 py-1 text-xs font-medium text-gray-900">
                {work.format_variant || '通用格式'}
              </span>
            </div>
            <div
              className="sf-script-rendered prose prose-invert max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gold-300"
              dangerouslySetInnerHTML={{
                __html: sanitizeHtml(work.resultHtml || '<p class="text-gray-500">暂无内容</p>'),
              }}
            />
          </section>
          <WorkMetaPanel work={work} themeName={theme.name} />
        </motion.div>

        {/* 进度时间线（如后端返回 progress HTML 则直接展示） */}
        {work.progressHtml && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-8 mb-8"
          >
            <div className="flex items-center gap-3 mb-6">
              <Clock className="w-5 h-5 text-brand-600" />
              <h2 className="text-2xl font-bold text-gray-900">创作历程</h2>
            </div>
            <div
              className="sf-progress-rendered"
              dangerouslySetInnerHTML={{ __html: sanitizeHtml(work.progressHtml) }}
            />
          </motion.div>
        )}

        {/* 底部 CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center"
        >
          <Button
            type="button"
            variant="ghost"
            size="lg"
            iconLeft={ArrowLeft}
            className="w-full sm:w-auto"
            onClick={() => navigate('/works')}
          >
            查看更多作品
          </Button>
          <Button
            type="button"
            variant="gold"
            size="lg"
            iconLeft={Sparkles}
            iconRight={ChevronRight}
            className="w-full sm:w-auto"
            onClick={() => navigate('/drama')}
          >
            创作新剧本
          </Button>
        </motion.div>

        {/* 分享弹窗 */}
        <AnimatePresence>
          {shareOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-navy-950/80 backdrop-blur-md z-50 flex items-center justify-center p-6"
              onClick={() => setShareOpen(false)}
            >
              <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="max-w-md w-full rounded-2xl border border-gray-200 bg-white border border-gray-200 shadow-sm p-8"
              >
                <div className="text-center mb-6">
                  <div className="w-16 h-16 rounded-2xl mx-auto mb-4 bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
                    <Share2 className="w-7 h-7 text-navy-950" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">分享作品</h3>
                  <p className="text-sm text-gray-500">复制链接分享给他人查看</p>
                </div>

                <div className="mb-5 rounded-xl border border-gray-200 bg-gray-50 p-4">
                  <p className="text-xs text-gray-400 mb-2">分享链接</p>
                  <p className="text-sm text-gray-700 font-mono break-all">
                    {shareLink || window.location.href}
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setShareOpen(false)}
                    className="flex-1 rounded-xl border border-gray-200 bg-gray-50 py-3 font-medium text-gray-900 transition-all hover:bg-gray-100"
                  >
                    关闭
                  </button>
                  <button
                    onClick={() => {
                      navigator.clipboard?.writeText(shareLink || window.location.href)
                      setCopied(true)
                      setTimeout(() => setCopied(false), 2000)
                    }}
                    className="flex-1 py-3 rounded-xl font-semibold btn-gold flex items-center justify-center gap-2"
                  >
                    {copied ? <Check className="w-4 h-4 text-navy-950" /> : <Copy className="w-4 h-4 text-navy-950" />}
                    {copied ? '已复制' : '复制链接'}
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </PageContainer>
    </div>
  )
}

function AgentList({ label, items }) {
  if (!items?.length) return null
  return (
    <div>
      <p className="text-xs text-gray-400 mb-2">{label}</p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-gray-700">
            · {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
