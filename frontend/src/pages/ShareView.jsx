import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Film,
  User,
  Calendar,
  Star,
  FileText,
  Sparkles,
  Lock,
  ArrowRight,
  Eye,
  Heart,
  Check,
} from 'lucide-react'
import { shareApi } from '@/services/api'

export default function ShareView() {
  const { token } = useParams()
  const [loading, setLoading] = useState(true)
  const [work, setWork] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await shareApi.view(token)
        const data = (res && res.data) || null
        if (!data || !data.title) {
          throw new Error('no data')
        }
        setWork(data)
      } catch (err) {
        // 作为 fallback：用构造的 mock 数据
        const isExpired =
          (err && err.message && err.message.toLowerCase().includes('expired')) ||
          (err && err.message && err.message.toLowerCase().includes('invalid'))
        if (isExpired) {
          setError('分享链接已过期或无效')
        } else {
          // 演示数据
          setWork({
            title: `分享作品 · ${token || 'demo'}`,
            author_nickname: '剧本创作者',
            created_at: new Date().toISOString(),
            expires_at: null,
            remain_views: 100,
            allow_download: false,
            rendered_share_html: `<div class="sf-share-preview"><h2 class="sf-title">✨ 剧本示例内容</h2><p>本页面内容由后端以预渲染 HTML 形式注入。</p><p>当前使用演示数据，可预览基本样式。</p></div>`,
          })
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [token])

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-950 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 border-4 border-gold-400/30 border-t-gold-400 rounded-full mx-auto mb-4"
          />
          <div className="text-navy-300">加载中…</div>
        </div>
      </div>
    )
  }

  if (!work && error) {
    return (
      <div className="min-h-screen bg-navy-950 flex items-center justify-center px-6">
        <div className="text-center">
          <Lock className="w-16 h-16 text-navy-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">{error}</h2>
          <p className="text-navy-300 mb-6">该分享链接不存在或已过期</p>
          <Link to="/" className="btn-gold inline-flex items-center gap-2">
            返回首页
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    )
  }

  if (!work) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-navy-950 via-navy-900 to-navy-950 relative">
      {/* 水印背景 */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-10">
        <div className="absolute -rotate-30 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white/[0.03] text-6xl font-bold whitespace-nowrap select-none">
          ScriptForge · 仅供预览
        </div>
      </div>

      {/* 顶部导航 */}
      <header className="relative z-20 border-b border-navy-700/40 bg-navy-950/90 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <motion.div
              whileHover={{ rotate: 10, scale: 1.1 }}
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
            >
              <Film className="w-5 h-5 text-white" />
            </motion.div>
            <span className="text-xl font-bold gradient-text">ScriptForge</span>
          </Link>

          <div className="flex items-center gap-3 text-sm text-navy-300">
            <Eye className="w-4 h-4" />
            <span>{work.remain_views != null ? `还可查看 ${work.remain_views} 次` : '分享作品'}</span>
          </div>
        </div>
      </header>

      {/* 水印提示条 */}
      <div className="relative z-20 bg-gold-500/10 border-b border-gold-500/20 text-center py-2">
        <span className="text-sm text-gold-400">🔒 本作品仅供预览，版权归属原创作者，未经许可不得转载或商用</span>
      </div>

      {/* 主要内容 */}
      <main className="relative z-20 max-w-4xl mx-auto px-6 py-12">
        {/* 作品头部 */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gold-500/20 border border-gold-500/30 text-gold-400 text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            精选剧本分享
          </div>

          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6 leading-tight">{work.title}</h1>

          {/* 作者信息 */}
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-950 font-bold">
              {String(work.author_nickname || '作者').charAt(0)}
            </div>
            <div className="text-left">
              <div className="text-white font-medium">{work.author_nickname || '匿名作者'}</div>
              <div className="text-xs text-navy-400 flex items-center gap-1.5">
                <Calendar className="w-3 h-3" />
                {formatDate(work.created_at)}
              </div>
            </div>
          </div>

          {/* 评分与统计 */}
          <div className="flex items-center justify-center gap-6 mt-6">
            <div className="flex items-center gap-2 text-gold-400">
              <Star className="w-5 h-5 fill-gold-400" />
              <span className="font-bold">推荐作品</span>
            </div>
            <div className="w-px h-4 bg-navy-700" />
            <div className="flex items-center gap-2 text-navy-300">
              <Eye className="w-4 h-4" />
              <span>AI 生成 · 已审核</span>
            </div>
          </div>
        </motion.div>

        {/* 内容卡片 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-3xl p-8 md:p-10 mb-8 relative"
        >
          {/* 重复水印 */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-3xl">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="absolute text-white/[0.02] text-sm font-bold whitespace-nowrap select-none"
                style={{
                  top: `${15 + i * 22}%`,
                  left: `${5 + (i % 2) * 35}%`,
                  transform: 'rotate(-20deg)',
                }}
              >
                ScriptForge 预览 · {token || 'share'}
              </div>
            ))}
          </div>

          {/* 正文（由后端预渲染 HTML 注入） */}
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-navy-700/40">
              <FileText className="w-5 h-5 text-gold-400" />
              <h2 className="text-2xl font-bold text-white">剧本预览</h2>
            </div>

            <div
              className="sf-script-rendered prose prose-invert max-w-none prose-headings:text-white prose-p:text-navy-100 prose-strong:text-gold-300"
              dangerouslySetInnerHTML={{ __html: work.rendered_share_html || '<p class="text-navy-300">暂无预览内容</p>' }}
            />
          </div>
        </motion.div>

        {/* CTA 注册按钮区 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card-gold rounded-3xl p-10 text-center relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-gold-500/10 via-transparent to-purple-500/10" />
          <div className="relative z-10">
            <motion.div
              animate={{ rotate: [0, 10, -10, 10, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              className="w-16 h-16 rounded-2xl mx-auto mb-6 flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
                boxShadow: '0 10px 40px -10px rgba(244, 183, 25, 0.5)',
              }}
            >
              <Sparkles className="w-8 h-8 text-navy-950" />
            </motion.div>

            <h2 className="text-3xl font-bold text-white mb-4">
              也想创作属于你的<span className="gradient-text">爆款剧本</span>？
            </h2>
            <p className="text-navy-200 text-lg mb-8 max-w-xl mx-auto">
              ScriptForge AI 让你从零开始，一句话创意即可生成完整可拍摄的A级剧本。
              加入创作者社区，体验 AI 赋能的专业剧本创作。
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/register"
                className="btn-gold text-lg inline-flex items-center justify-center gap-2 !py-4 !px-10"
              >
                <User className="w-5 h-5" />
                免费注册使用
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/"
                className="btn-ghost text-lg inline-flex items-center justify-center gap-2 !py-4 !px-10"
              >
                了解更多
              </Link>
            </div>

            <div className="mt-8 flex items-center justify-center gap-8 text-sm text-navy-400">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400" />
                无需信用卡
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400" />
                3次免费创作
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400" />
                即注册即用
              </div>
            </div>
          </div>
        </motion.div>

        {/* 底部声明 */}
        <div className="mt-12 text-center text-sm text-navy-500">
          <p className="mb-2">本作品由 ScriptForge AI 辅助创作，版权归原创作者所有</p>
          <p>© 2026 ScriptForge · 保留所有权利</p>
        </div>
      </main>
    </div>
  )
}

function formatDate(val) {
  if (!val) return '—'
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return String(val).slice(0, 10)
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  } catch (e) {
    return String(val).slice(0, 10)
  }
}
