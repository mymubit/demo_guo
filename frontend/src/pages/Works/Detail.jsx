import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Download,
  Share2,
  Copy,
  Check,
  Film,
  Calendar,
  Clock,
  FileText,
  Sparkles,
  Star,
  Users,
  ChevronRight,
  RefreshCw,
} from 'lucide-react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { works as worksApi, creation } from '@/services/api'
import { formatDateTime } from '@/utils/date'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import ScoreReport from '@/components/creation/ScoreReport'
import GateReport from '@/components/creation/GateReport'
import WorkVisualizationSection from '@/components/works/WorkVisualizationSection'
import { ExecutionDurationLabel } from '@/components/shared/ExecutionRunPanel'

import { getThemeMeta } from '@/constants/themeMeta'
import ThemeBadge from '@/components/ui/ThemeBadge'

import { getWorkStatusMeta } from '@/utils/workStatus'
import { useWorkDetail } from '@/hooks/queries/useWorkDetail'

function statusBadge(status, work = {}) {
  const meta = getWorkStatusMeta(status, work)
  const tone =
    meta.key === 'completed'
      ? 'bg-green-500/15 text-green-400'
      : meta.key === 'generating'
        ? 'bg-gold-500/15 text-gold-400'
        : meta.key === 'failed'
          ? 'bg-red-500/15 text-red-400'
          : meta.key === 'awaiting'
            ? 'bg-blue-500/15 text-blue-300'
            : 'bg-navy-400/15 text-navy-200'
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
  const [agentRunning, setAgentRunning] = useState(null)
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

  const handleRunAgent = async (agentId) => {
    if (!work?.project_id) return
    setAgentRunning(agentId)
    try {
      const res = await worksApi.runAgent(work.project_id, agentId)
      if (res?.status === 'error') {
        throw new Error((res.errors || []).join('；') || 'Agent 执行失败')
      }
      toast.success(agentId === 'insight' ? '拉片分析完成' : '宣发物料已生成')
      await reloadWork()
    } catch (err) {
      toast.error(err.message || '执行失败')
    } finally {
      setAgentRunning(null)
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
          <h2 className="text-2xl font-bold text-white mb-4">作品不存在</h2>
          <p className="text-navy-300 mb-6">{loadError || '找不到该作品或您无权限访问'}</p>
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
      <div className="particles-bg" />
      <div className="max-w-5xl mx-auto px-6 relative z-10">
        {/* 返回导航 */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <button
            onClick={() => navigate('/works')}
            className="inline-flex items-center gap-2 text-navy-300 hover:text-gold-400 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>返回作品列表</span>
          </button>
        </motion.div>

        {/* 头部信息卡 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-3xl p-8 mb-8 relative overflow-hidden"
        >
          <div
            className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-20 blur-3xl pointer-events-none"
            style={{ background: theme.color, transform: 'translate(30%, -30%)' }}
          />

          <div className="relative">
            {/* 徽章 */}
            <div className="flex flex-wrap items-center gap-3 mb-5">
              <ThemeBadge theme={theme} size="md" className="!px-4 !py-2" />
              {work.overall_score != null ? (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/15 text-gold-400">
                  <Star className="w-4 h-4 fill-gold-400" />
                  <span className="text-sm font-bold">
                    {work.overall_score} 分 · {work.grade || '—'}
                  </span>
                </div>
              ) : (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/15 text-gold-400">
                  <Star className="w-4 h-4 fill-gold-400" />
                  <span className="text-sm font-bold">{work.progress_percent || 0}%</span>
                </div>
              )}
              {work.fusion_status === 'ready' && (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-green-500/15 text-green-400">
                  <span className="text-sm font-semibold">可发布</span>
                </div>
              )}
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl ${statusInfo.cls}`}>
                <span className="text-sm font-semibold">{statusInfo.text}</span>
              </div>
            </div>

            {/* 标题 */}
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">
              {work.title || '未命名剧本'}
            </h1>

            {/* 元信息 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <MetaItem icon={Film} label="集数" value={`${work.episode_count || 0} 集`} />
              <MetaItem icon={FileText} label="格式" value={work.format_variant || '通用'} />
              <MetaItem icon={Calendar} label="创建时间" value={formatDateTime(work.created_at)} />
              <MetaItem
                icon={Sparkles}
                label="项目ID"
                value={work.project_id.toString().slice(0, 12)}
              />
            </div>

            {/* 操作按钮组 */}
            <div className="flex flex-wrap gap-3">
              {work.status !== 'completed' && work.project_id && (
                <button
                  onClick={() => navigate(`/creation?project=${work.project_id}`)}
                  className="px-5 py-3 rounded-xl font-semibold flex items-center gap-2 btn-gold"
                >
                  <Sparkles className="w-4 h-4" />
                  继续编辑
                </button>
              )}
              <button
                onClick={() => handleDownload('md')}
                disabled={work.status !== 'completed'}
                className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/50 hover:bg-navy-700 text-white transition-all border border-navy-600/30 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="w-4 h-4" />
                下载 Markdown
                {downloading === 'md' && <span className="text-xs">处理中…</span>}
              </button>
              <button
                onClick={() => handleDownload('html')}
                disabled={work.status !== 'completed'}
                className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/50 hover:bg-navy-700 text-white transition-all border border-navy-600/30 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="w-4 h-4" />
                下载 HTML
                {downloading === 'html' && <span className="text-xs">处理中…</span>}
              </button>
              <button
                onClick={handleCopy}
                className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/50 hover:bg-navy-700 text-white transition-all border border-navy-600/30"
              >
                {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                {copied ? '已复制链接' : '复制链接'}
              </button>
              <button
                onClick={handleShare}
                disabled={work.status !== 'completed' || sharing}
                className="px-5 py-3 rounded-xl font-semibold flex items-center gap-2 btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all disabled:opacity-50"
              >
                <Share2 className="w-4 h-4" />
                {sharing ? '生成中…' : '分享作品'}
              </button>
              <button
                onClick={() => navigate('/creation')}
                className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/50 hover:bg-navy-700 text-white transition-all border border-navy-600/30"
              >
                <RefreshCw className="w-4 h-4" />
                创作新剧本
              </button>
            </div>
          </div>
        </motion.div>

        {(work.status === 'completed' || work.fusionSnapshot?.agentArtifacts) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.11 }}
            className="glass-card rounded-3xl p-8 mb-8"
          >
            <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-gold-400" />
                智能分析
              </h2>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={agentRunning != null}
                  onClick={() => handleRunAgent('insight')}
                  className="px-4 py-2 rounded-xl text-sm font-medium bg-navy-700/50 hover:bg-navy-700 text-white border border-navy-600/30 disabled:opacity-50"
                >
                  {agentRunning === 'insight' ? '分析中…' : '拉片分析'}
                </button>
                <button
                  type="button"
                  disabled={agentRunning != null}
                  onClick={() => handleRunAgent('marketing')}
                  className="px-4 py-2 rounded-xl text-sm font-medium btn-gold disabled:opacity-50"
                >
                  {agentRunning === 'marketing' ? '生成中…' : '宣发物料'}
                </button>
                <button
                  type="button"
                  disabled={agentRunning != null}
                  onClick={() => handleRunAgent('review')}
                  className="px-4 py-2 rounded-xl text-sm font-medium bg-navy-700/50 hover:bg-navy-700 text-white border border-navy-600/30 disabled:opacity-50"
                >
                  {agentRunning === 'review' ? '质检中…' : '重新质检'}
                </button>
                <button
                  type="button"
                  disabled={agentRunning != null}
                  onClick={() => handleRunAgent('polish')}
                  className="px-4 py-2 rounded-xl text-sm font-medium bg-navy-700/50 hover:bg-navy-700 text-white border border-navy-600/30 disabled:opacity-50"
                >
                  {agentRunning === 'polish' ? '分析中…' : '润色建议'}
                </button>
              </div>
            </div>

            {work.fusionSnapshot?.agentArtifacts?.score?.overallScore != null && (
              <div className="mb-6 rounded-2xl bg-navy-800/30 border border-navy-700/30 p-5">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <h3 className="text-sm font-semibold text-gold-400">深度评分</h3>
                  <ExecutionDurationLabel
                    durationMs={work.fusionSnapshot.agentArtifacts.score.durationMs}
                    className="text-[10px]"
                  />
                </div>
                <p className="text-sm text-navy-200 mb-2">
                  综合 {work.fusionSnapshot.agentArtifacts.score.overallScore ?? '—'} 分
                  {work.fusionSnapshot.agentArtifacts.score.grade
                    ? ` · ${work.fusionSnapshot.agentArtifacts.score.grade} 级`
                    : ''}
                </p>
              </div>
            )}

            {work.fusionSnapshot?.agentArtifacts?.review && (
              <div className="mb-6 rounded-2xl bg-navy-800/30 border border-navy-700/30 p-5">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <h3 className="text-sm font-semibold text-gold-400">质检报告</h3>
                  <ExecutionDurationLabel
                    durationMs={work.fusionSnapshot.agentArtifacts.review.durationMs}
                    className="text-[10px]"
                  />
                </div>
                <p className="text-sm text-navy-200 mb-2">
                  状态：{work.fusionSnapshot.agentArtifacts.review.passed ? '通过' : '待优化'}
                  {work.fusionSnapshot.agentArtifacts.review.pacingPassed === false && ' · 节奏需调整'}
                </p>
                {(work.fusionSnapshot.agentArtifacts.review.issues || []).length > 0 && (
                  <ul className="space-y-1 text-sm text-navy-300 mb-3">
                    {work.fusionSnapshot.agentArtifacts.review.issues.map((issue, i) => (
                      <li key={i}>· {issue}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {(work.fusionSnapshot?.agentArtifacts?.polish?.suggestions || []).length > 0 && (
              <div className="mb-6 rounded-2xl bg-navy-800/30 border border-navy-700/30 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                  <h3 className="text-sm font-semibold text-gold-400">润色建议</h3>
                  <div className="flex items-center gap-3">
                    <ExecutionDurationLabel
                      durationMs={work.fusionSnapshot.agentArtifacts.polish.durationMs}
                      className="text-[10px]"
                    />
                    {work.fusionSnapshot.agentArtifacts.polish.applied && (
                      <span className="text-xs text-green-400">已应用部分建议</span>
                    )}
                  </div>
                </div>
                <ul className="space-y-2 mb-4">
                  {work.fusionSnapshot.agentArtifacts.polish.suggestions.map((s) => (
                    <li
                      key={s.index}
                      className="flex gap-3 items-start text-sm text-navy-200 rounded-lg bg-navy-900/40 p-3"
                    >
                      <input
                        type="checkbox"
                        checked={selectedPolish.has(s.index)}
                        onChange={() => togglePolishIndex(s.index)}
                        className="mt-1 rounded border-navy-600"
                      />
                      <div className="min-w-0 flex-1">
                        {s.episodeNumber != null && (
                          <span className="text-xs text-gold-400/90 mr-2">第{s.episodeNumber}集</span>
                        )}
                        {s.field && <span className="text-xs text-navy-500 mr-2">{s.field}</span>}
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
                    className="px-4 py-2 rounded-xl text-sm font-medium bg-navy-700/50 text-white border border-navy-600/30 disabled:opacity-50"
                  >
                    全部应用
                  </button>
                </div>
              </div>
            )}

            {work.fusionSnapshot?.agentArtifacts?.insight?.lineCount > 0 && (
              <div className="mb-6 rounded-2xl bg-navy-800/30 border border-navy-700/30 p-5">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <h3 className="text-sm font-semibold text-gold-400">拉片报告</h3>
                  <ExecutionDurationLabel
                    durationMs={work.fusionSnapshot.agentArtifacts.insight.durationMs}
                    className="text-[10px]"
                  />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <AgentStat label="剧本行数" value={work.fusionSnapshot.agentArtifacts.insight.lineCount} />
                  <AgentStat
                    label="集标题数"
                    value={work.fusionSnapshot.agentArtifacts.insight.episodeHeadings}
                  />
                </div>
                {work.fusionSnapshot.agentArtifacts.insight.rhythmNotes && (
                  <p className="text-sm text-navy-200 leading-relaxed">
                    {work.fusionSnapshot.agentArtifacts.insight.rhythmNotes}
                  </p>
                )}
                {(work.fusionSnapshot.agentArtifacts.insight.hookPoints || []).length > 0 && (
                  <ul className="mt-3 space-y-1 text-sm text-navy-300">
                    {work.fusionSnapshot.agentArtifacts.insight.hookPoints.map((h, i) => (
                      <li key={i}>· {typeof h === 'string' ? h : JSON.stringify(h)}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {(work.fusionSnapshot?.agentArtifacts?.marketing?.titles || []).length > 0 && (
              <div className="rounded-2xl bg-navy-800/30 border border-navy-700/30 p-5">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <h3 className="text-sm font-semibold text-gold-400">宣发物料</h3>
                  <ExecutionDurationLabel
                    durationMs={work.fusionSnapshot.agentArtifacts.marketing.durationMs}
                    className="text-[10px]"
                  />
                </div>
                <div className="space-y-3">
                  <AgentList label="推荐标题" items={work.fusionSnapshot.agentArtifacts.marketing.titles} />
                  <AgentList label="切片钩子" items={work.fusionSnapshot.agentArtifacts.marketing.clipHooks} />
                  <AgentList label="海报 Slogan" items={work.fusionSnapshot.agentArtifacts.marketing.posterSlogans} />
                </div>
              </div>
            )}

            {!work.fusionSnapshot?.agentArtifacts?.insight?.lineCount &&
              !(work.fusionSnapshot?.agentArtifacts?.marketing?.titles || []).length && (
                <p className="text-sm text-navy-400">
                  剧本完成后可运行拉片分析或生成宣发物料（宣发通常在剧本后处理链自动生成）。
                </p>
              )}
          </motion.div>
        )}

        {work.gateSummary && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="glass-card rounded-3xl p-8 mb-8"
          >
            <h2 className="text-2xl font-bold text-white mb-4">逐集质检</h2>
            <GateReport summary={work.gateSummary} />
          </motion.div>
        )}

        {work.scoreReport && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="glass-card rounded-3xl p-8 mb-8"
          >
            <h2 className="text-2xl font-bold text-white mb-4">8 维评分</h2>
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

        {/* 剧本正文（直接插入后端返回的预渲染 HTML） */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card rounded-3xl p-6 md:p-10 mb-8"
        >
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-navy-700/40">
            <FileText className="w-5 h-5 text-gold-400" />
            <h2 className="text-2xl font-bold text-white">剧本内容</h2>
          </div>
          <div
            className="sf-script-rendered prose prose-invert max-w-none prose-headings:text-white prose-p:text-navy-100 prose-strong:text-gold-300"
            dangerouslySetInnerHTML={{
              __html: sanitizeHtml(work.resultHtml || '<p class="text-navy-300">暂无内容</p>'),
            }}
          />
        </motion.div>

        {/* 进度时间线（如后端返回 progress HTML 则直接展示） */}
        {work.progressHtml && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card rounded-3xl p-8 mb-8"
          >
            <div className="flex items-center gap-3 mb-6">
              <Clock className="w-5 h-5 text-gold-400" />
              <h2 className="text-2xl font-bold text-white">创作历程</h2>
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
          className="mt-8 flex flex-col md:flex-row gap-3 justify-center"
        >
          <button
            onClick={() => navigate('/works')}
            className="px-8 py-4 rounded-2xl font-semibold flex items-center justify-center gap-2 bg-navy-700/40 hover:bg-navy-700/60 text-white transition-all border border-navy-600/30"
          >
            <ArrowLeft className="w-5 h-5" />
            查看更多作品
          </button>
          <button
            onClick={() => navigate('/creation')}
            className="px-8 py-4 rounded-2xl font-semibold flex items-center justify-center gap-2 btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all"
          >
            <Sparkles className="w-5 h-5" />
            创作新剧本
            <ChevronRight className="w-5 h-5" />
          </button>
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
                className="glass-card rounded-3xl p-8 max-w-md w-full border border-navy-600/30"
              >
                <div className="text-center mb-6">
                  <div className="w-16 h-16 rounded-2xl mx-auto mb-4 bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
                    <Share2 className="w-7 h-7 text-navy-950" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">分享作品</h3>
                  <p className="text-sm text-navy-300">复制链接分享给他人查看</p>
                </div>

                <div className="bg-navy-800/50 rounded-xl p-4 mb-5 border border-navy-600/30">
                  <p className="text-xs text-navy-400 mb-2">分享链接</p>
                  <p className="text-sm text-navy-100 font-mono break-all">
                    {shareLink || window.location.href}
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setShareOpen(false)}
                    className="flex-1 py-3 rounded-xl font-medium bg-navy-700/50 hover:bg-navy-700 text-white transition-all"
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
      </div>
    </div>
  )
}

function AgentStat({ label, value }) {
  return (
    <div className="bg-navy-900/40 rounded-xl p-3 border border-navy-700/20">
      <p className="text-[10px] text-navy-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-white font-semibold text-sm">{value ?? '—'}</p>
    </div>
  )
}

function AgentList({ label, items }) {
  if (!items?.length) return null
  return (
    <div>
      <p className="text-xs text-navy-500 mb-2">{label}</p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-navy-100">
            · {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

function MetaItem({ icon: Icon, label, value }) {
  return (
    <div className="bg-navy-800/30 rounded-xl p-4 border border-navy-600/20">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-3.5 h-3.5 text-gold-400" />
        <span className="text-xs text-navy-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-white font-semibold text-sm">{value}</div>
    </div>
  )
}
