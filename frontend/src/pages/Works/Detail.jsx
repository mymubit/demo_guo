import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
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
  X,
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
import { cn } from '@/utils/cn'
import { getThemeMeta } from '@/constants/themeMeta'
import ThemeBadge from '@/components/ui/ThemeBadge'
import { Button, Card, Badge } from '@/components/ui'
import PageShell from '@/components/layout/PageShell'
import { getWorkStatusMeta } from '@/utils/workStatus'
import { useWorkDetail } from '@/hooks/queries/useWorkDetail'

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
      <PageShell title="" showBack={false}>
        <div className="min-h-[60vh] flex items-center justify-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 rounded-full border-4 border-gold-400 border-t-transparent"
          />
        </div>
      </PageShell>
    )
  }

  if (!work) {
    return (
      <PageShell title="作品不存在" backTo="/works">
        <div className="max-w-3xl mx-auto text-center py-16">
          <p className="text-slate-400 mb-6">{loadError || '找不到该作品或您无权限访问'}</p>
          <Button variant="gold" onClick={() => navigate('/works')}>
            返回作品列表
          </Button>
        </div>
      </PageShell>
    )
  }

  const theme = getThemeMeta(work.theme)
  const meta = getWorkStatusMeta(work.status, work)

  const headerActions = (
    <div className="flex flex-wrap gap-2">
      {work.status !== 'completed' && work.project_id && (
        <Button
          variant="gold"
          iconLeft={<Sparkles className="w-4 h-4" />}
          onClick={() => navigate(work.drama_workspace_url || `/drama/workspace/${work.project_id}`)}
        >
          继续编辑
        </Button>
      )}
      <Button
        variant="secondary"
        iconLeft={<Download className="w-4 h-4" />}
        disabled={work.status !== 'completed'}
        onClick={() => handleDownload('md')}
        isLoading={downloading === 'md'}
      >
        MD 导出
      </Button>
      <Button
        variant="secondary"
        iconLeft={<Download className="w-4 h-4" />}
        disabled={work.status !== 'completed'}
        onClick={() => handleDownload('html')}
        isLoading={downloading === 'html'}
      >
        HTML 导出
      </Button>
      <Button
        variant="secondary"
        iconLeft={copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
        onClick={handleCopy}
      >
        {copied ? '已复制' : '复制链接'}
      </Button>
      <Button
        variant="gold"
        iconLeft={<Share2 className="w-4 h-4" />}
        disabled={work.status !== 'completed' || sharing}
        onClick={handleShare}
        isLoading={sharing}
      >
        分享
      </Button>
    </div>
  )

  return (
    <PageShell
      title={work.title || '未命名剧本'}
      backTo="/works"
      maxWidth="xl"
      actions={headerActions}
    >
      <div
        className="relative h-40 md:h-48 rounded-2xl mb-6 overflow-hidden"
        style={{
          background: `linear-gradient(135deg, ${theme.color}44 0%, #0a0e1a 55%, #050810 100%)`,
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-t from-navy-950 via-navy-950/40 to-transparent" />
        <div className="absolute bottom-5 left-5 right-5 flex flex-wrap items-end justify-between gap-4">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <ThemeBadge theme={theme} size="sm" />
              {work.overall_score != null ? (
                <Badge tone="gold" size="sm">
                  <Star className="h-3 w-3 mr-1 fill-gold-500" />
                  {work.overall_score} 分 · {work.grade || '—'}
                </Badge>
              ) : (
                <Badge tone="info" size="sm">
                  {work.progress_percent || 0}% 生成中
                </Badge>
              )}
              <Badge tone={meta.tone || 'default'} size="sm">
                {meta.label}
              </Badge>
              {(work.drama_stage === 'ready' || work.drama?.delivery_status === 'ready') && (
                <Badge tone="success" size="sm">可发布</Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      <p className="text-sm text-slate-400 mb-8 -mt-4">
        {theme.name} · {work.episode_count || 0} 集 · {work.format_variant || '通用'} · {formatDateTime(work.created_at)}
      </p>

      {(work.status === 'completed' || work.scoreReport || work.gateSummary || work.reviewReport || work.marketingKit) && (
        <Card variant="glass" padding="lg" className="mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-gold-400" />
              智能分析
            </h2>
          </div>

          {work.projectBrief?.workingTitle && (
            <div className="mb-6 rounded-xl bg-white/5 border border-white/10 p-4">
              <h3 className="text-sm font-semibold text-gold-400 mb-2">项目简报</h3>
              <p className="text-sm text-slate-300">
                {work.projectBrief.workingTitle}
                {work.projectBrief.episodeCount != null && ` · ${work.projectBrief.episodeCount} 集`}
              </p>
              {work.projectBrief.writingBrief && (
                <p className="text-sm text-slate-400 mt-2 line-clamp-3">{work.projectBrief.writingBrief}</p>
              )}
            </div>
          )}

          {work.scoreReport?.overallScore != null && (
            <div className="mb-6 rounded-xl bg-white/5 border border-white/10 p-4">
              <h3 className="text-sm font-semibold text-gold-400 mb-2">深度评分</h3>
              <p className="text-sm text-slate-300">
                综合 {work.scoreReport.overallScore ?? '—'} 分
                {work.scoreReport.grade ? ` · ${work.scoreReport.grade} 级` : ''}
              </p>
            </div>
          )}

          {work.reviewReport && (
            <div className="mb-6 rounded-xl bg-white/5 border border-white/10 p-4">
              <h3 className="text-sm font-semibold text-gold-400 mb-2">质检报告</h3>
              <p className="text-sm text-slate-300 mb-2">
                状态：{work.reviewReport.passed ? <span className="text-emerald-400">通过</span> : <span className="text-amber-400">待优化</span>}
                {work.reviewReport.pacingPassed === false && ' · 节奏需调整'}
              </p>
              {(work.reviewReport.issues || []).length > 0 && (
                <ul className="space-y-1 text-sm text-slate-400">
                  {work.reviewReport.issues.map((issue, i) => (
                    <li key={i}>· {typeof issue === 'string' ? issue : issue.message || JSON.stringify(issue)}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {(work.polishLog?.suggestions || []).length > 0 && (
            <div className="mb-6 rounded-xl bg-white/5 border border-white/10 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                <h3 className="text-sm font-semibold text-gold-400">润色建议</h3>
                {work.polishLog.applied && (
                  <span className="text-xs text-emerald-400">已应用部分建议</span>
                )}
              </div>
              <ul className="space-y-2 mb-4">
                {work.polishLog.suggestions.map((s) => (
                  <li
                    key={s.index ?? s.advice}
                    className="flex items-start gap-3 rounded-lg bg-white/[0.03] border border-white/5 p-3 text-sm text-slate-300"
                  >
                    <input
                      type="checkbox"
                      checked={selectedPolish.has(s.index)}
                      onChange={() => togglePolishIndex(s.index)}
                      className="mt-1 rounded border-white/20 bg-white/5 accent-gold-500"
                    />
                    <div className="min-w-0 flex-1">
                      {s.episodeNumber != null && (
                        <span className="text-xs text-gold-400 mr-2">第{s.episodeNumber}集</span>
                      )}
                      {s.field && <span className="text-xs text-slate-500 mr-2">{s.field}</span>}
                      <p className="whitespace-pre-wrap">{s.advice}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="gold"
                  size="sm"
                  disabled={polishApplying || selectedPolish.size === 0}
                  onClick={() => handleApplyPolish(false)}
                  isLoading={polishApplying}
                >
                  应用选中（{selectedPolish.size}）
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={polishApplying}
                  onClick={() => handleApplyPolish(true)}
                >
                  全部应用
                </Button>
              </div>
            </div>
          )}

          {(work.marketingKit?.titles || []).length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 p-4">
              <h3 className="text-sm font-semibold text-gold-400 mb-3">宣发物料</h3>
              <div className="space-y-3">
                <AgentList label="推荐标题" items={work.marketingKit.titles} />
                <AgentList label="切片钩子" items={work.marketingKit.clipHooks} />
                <AgentList label="海报 Slogan" items={work.marketingKit.posterSlogans} />
              </div>
            </div>
          )}

          {!work.scoreReport?.overallScore && !work.reviewReport && !(work.marketingKit?.titles || []).length && !(work.polishLog?.suggestions || []).length && (
            <p className="text-sm text-slate-500">
              暂无智能分析结果，请在创作工作台运行独立 Agent。
            </p>
          )}
        </Card>
      )}

      {work.gateSummary && (
        <Card variant="glass" padding="lg" className="mb-6">
          <h2 className="text-xl font-bold text-white mb-4">逐集质检</h2>
          <GateReport summary={work.gateSummary} />
        </Card>
      )}

      {work.scoreReport && (
        <Card variant="glass" padding="lg" className="mb-6">
          <h2 className="text-xl font-bold text-white mb-4">8 维评分</h2>
          <ScoreReport report={work.scoreReport} />
        </Card>
      )}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18 }}
        className="mb-6"
      >
        <WorkVisualizationSection projectId={work.project_id} />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8 grid grid-cols-1 gap-5 lg:grid-cols-[1fr_320px]"
      >
        <Card variant="glass" padding="lg">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-gold-400" />
              <h2 className="text-xl font-bold text-white">剧本内容</h2>
            </div>
            <Badge tone="gold" variant="subtle" size="sm">
              {work.format_variant || '通用格式'}
            </Badge>
          </div>
          <div
            className="sf-script-rendered prose prose-invert max-w-none prose-headings:text-white prose-p:text-slate-300 prose-strong:text-gold-300"
            dangerouslySetInnerHTML={{
              __html: sanitizeHtml(work.resultHtml || '<p class="text-slate-500">暂无内容</p>'),
            }}
          />
        </Card>
        <WorkMetaPanel work={work} themeName={theme.name} />
      </motion.div>

      {work.progressHtml && (
        <Card variant="glass" padding="lg" className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Clock className="w-5 h-5 text-gold-400" />
            <h2 className="text-xl font-bold text-white">创作历程</h2>
          </div>
          <div
            className="sf-progress-rendered"
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(work.progressHtml) }}
          />
        </Card>
      )}

      <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center pb-20 sm:pb-8">
        <Button
          type="button"
          variant="secondary"
          size="lg"
          className="w-full sm:w-auto"
          onClick={() => navigate('/works')}
        >
          查看更多作品
        </Button>
        <Button
          type="button"
          variant="gold"
          size="lg"
          iconRight={<ChevronRight className="w-4 h-4" />}
          className="w-full sm:w-auto"
          onClick={() => navigate('/drama')}
        >
          创作新剧本
        </Button>
      </div>

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
              className="max-w-md w-full rounded-2xl border border-white/10 bg-navy-900 backdrop-blur-xl p-8 relative"
            >
              <button
                onClick={() => setShareOpen(false)}
                className="absolute top-4 right-4 p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
              <div className="text-center mb-6">
                <div className="w-16 h-16 rounded-2xl mx-auto mb-4 bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
                  <Share2 className="w-7 h-7 text-navy-950" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">分享作品</h3>
                <p className="text-sm text-slate-400">复制链接分享给他人查看</p>
              </div>

              <div className="mb-5 rounded-xl bg-white/5 border border-white/10 p-4">
                <p className="text-xs text-slate-500 mb-2">分享链接</p>
                <p className="text-sm text-slate-300 font-mono break-all">
                  {shareLink || window.location.href}
                </p>
              </div>

              <div className="flex gap-3">
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={() => setShareOpen(false)}
                >
                  关闭
                </Button>
                <Button
                  variant="gold"
                  className="flex-1"
                  onClick={() => {
                    navigator.clipboard?.writeText(shareLink || window.location.href)
                    setCopied(true)
                    setTimeout(() => setCopied(false), 2000)
                  }}
                >
                  {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                  {copied ? '已复制' : '复制链接'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageShell>
  )
}

function AgentList({ label, items }) {
  if (!items?.length) return null
  return (
    <div>
      <p className="text-xs text-slate-500 mb-2">{label}</p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-slate-300">
            · {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
