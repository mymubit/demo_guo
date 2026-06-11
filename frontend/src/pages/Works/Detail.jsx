import { useState, useEffect } from 'react'
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
import { worksApi } from '@/services/api'

const THEME_META = {
  'family-revenge': { name: '家庭伦理复仇', emoji: '⚔️', color: '#e53e3e' },
  'overbearing-ceo': { name: '豪门霸总', emoji: '💎', color: '#d69e2e' },
  'sweet-pet': { name: '甜宠虐恋', emoji: '💕', color: '#d53f8c' },
  'time-travel': { name: '穿越重生', emoji: '⏰', color: '#805ad5' },
  'urban-rebirth': { name: '都市逆袭', emoji: '🏙️', color: '#3182ce' },
  'ancient-costume': { name: '古装权谋', emoji: '⚜️', color: '#2f855a' },
  'suspense-reversal': { name: '悬疑反转', emoji: '🕵️', color: '#5a67d8' },
  'mixed-theme': { name: '混合题材', emoji: '🎭', color: '#dd6b20' },
}

function formatDate(val) {
  if (!val) return '—'
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return String(val).slice(0, 16)
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch (e) {
    return String(val).slice(0, 16)
  }
}

function getThemeMeta(theme) {
  return (
    THEME_META[theme] ||
    THEME_META['mixed-theme'] || {
      name: theme || '未分类',
      emoji: '🎬',
      color: '#888',
    }
  )
}

function statusBadge(status) {
  switch (status) {
    case 'completed':
      return { text: '已完成', cls: 'bg-green-500/15 text-green-400' }
    case 'running':
      return { text: '创作中', cls: 'bg-gold-500/15 text-gold-400' }
    case 'pending':
      return { text: '待开始', cls: 'bg-navy-400/15 text-navy-200' }
    case 'failed':
      return { text: '创作失败', cls: 'bg-red-500/15 text-red-400' }
    default:
      return { text: status || '未知', cls: 'bg-navy-400/15 text-navy-200' }
  }
}

export default function WorksDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [work, setWork] = useState(null)
  const [loading, setLoading] = useState(true)
  const [useMock, setUseMock] = useState(false)
  const [copied, setCopied] = useState(false)
  const [shareOpen, setShareOpen] = useState(false)
  const [shareLink, setShareLink] = useState('')
  const [sharing, setSharing] = useState(false)
  const [downloading, setDownloading] = useState(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await worksApi.getDetail(id)
        const data = (res && res.data) || null
        if (!data || !data.title) {
          throw new Error('no data')
        }
        setWork(data)
      } catch (err) {
        // fallback 到 mock 数据，保证页面可预览
        const mock = {
          project_id: id,
          title: `剧本创作作品 · ${id?.slice(0, 6) || 'demo'}`,
          theme: 'overbearing-ceo',
          episode_count: 30,
          format_variant: 'B',
          status: 'completed',
          status_text: '已完成',
          progress_percent: 100,
          created_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
          rendered_result_html: `<div class="sf-preview"><h2 class="sf-title">✨ ${'剧本示例内容'}</h2><p>本页面内容由后端预渲染后注入。正在加载示例内容……</p></div>`,
          rendered_progress_html: '',
        }
        setWork(mock)
        setUseMock(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

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
      // 直接打开后端下载链接（由后端返回 FileResponse）
      const url = `/api/creation/download/${work.project_id}/?format=${type}`
      const a = document.createElement('a')
      a.href = url
      a.download = `${work.title || 'script'}.${type}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    } finally {
      setTimeout(() => setDownloading(null), 800)
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
      const link = (res && res.data && res.data.share_url) || `${window.location.origin}/share/${res?.data?.share_token || ''}`
      setShareLink(link)
    } catch (err) {
      // 用当前页面地址作为 fallback
      setShareLink(window.location.href.replace(/\/works\//, '/share/'))
    } finally {
      setSharing(false)
      setShareOpen(true)
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
          <p className="text-navy-300 mb-6">找不到该作品或您无权限访问</p>
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
  const statusInfo = statusBadge(work.status)

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
              <div
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl"
                style={{ background: theme.color + '20', color: theme.color }}
              >
                <span className="text-xl">{theme.emoji}</span>
                <span className="text-sm font-semibold">{theme.name}</span>
              </div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/15 text-gold-400">
                <Star className="w-4 h-4 fill-gold-400" />
                <span className="text-sm font-bold">
                  {work.progress_percent || 0}%
                </span>
              </div>
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl ${statusInfo.cls}`}>
                <span className="text-sm font-semibold">{statusInfo.text}</span>
              </div>
              {useMock && (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-navy-700/40 text-navy-300">
                  <span className="text-xs">演示数据</span>
                </div>
              )}
            </div>

            {/* 标题 */}
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">
              {work.title || '未命名剧本'}
            </h1>

            {/* 元信息 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <MetaItem icon={Film} label="集数" value={`${work.episode_count || 0} 集`} />
              <MetaItem icon={FileText} label="格式" value={work.format_variant || '通用'} />
              <MetaItem icon={Calendar} label="创建时间" value={formatDate(work.created_at)} />
              <MetaItem
                icon={Sparkles}
                label="项目ID"
                value={(work.project_id || id || '').toString().slice(0, 12)}
              />
            </div>

            {/* 操作按钮组 */}
            <div className="flex flex-wrap gap-3">
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
            dangerouslySetInnerHTML={{ __html: work.rendered_result_html || '<p class="text-navy-300">暂无内容</p>' }}
          />
        </motion.div>

        {/* 进度时间线（如后端返回 progress HTML 则直接展示） */}
        {work.rendered_progress_html && (
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
              dangerouslySetInnerHTML={{ __html: work.rendered_progress_html }}
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
