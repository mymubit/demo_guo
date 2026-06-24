import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Calendar,
  Star,
  FileText,
  Sparkles,
  Lock,
  ArrowRight,
  Eye,
  ShieldCheck,
} from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { share } from '@/services/api'
import { formatDate } from '@/utils/date'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import BrandLogo from '@/components/ui/BrandLogo'
import UserAvatar from '@/components/ui/UserAvatar'
import { ICON } from '@/constants/iconSizes'

export default function ShareView() {
  const { token } = useParams()
  const [loading, setLoading] = useState(true)
  const [work, setWork] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const data = await share.view(token)
        if (!data?.title && !data?.rendered_share_html) {
          throw new Error('分享内容不存在')
        }
        setWork(data)
      } catch (err) {
        setError(err.message || '分享链接已过期或无效')
        setWork(null)
      } finally {
        setLoading(false)
      }
    }
    if (token) load()
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
          <div className="text-slate-400">加载中…</div>
        </div>
      </div>
    )
  }

  if (!work && error) {
    return (
      <div className="min-h-screen bg-navy-950 flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 rounded-2xl bg-white/[0.03] border border-white/10 flex items-center justify-center mx-auto mb-6">
            <Lock className="w-10 h-10 text-slate-500" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">{error}</h2>
          <p className="text-slate-400 mb-8">该分享链接不存在或已过期</p>
          <Link to="/">
            <Button variant="gold" iconRight={<ArrowRight className="w-4 h-4" />}>
              返回首页
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  if (!work) {
    return null
  }

  return (
    <div className="min-h-screen bg-navy-950 text-white">
      <div className="border-b border-white/10 bg-white/[0.02] backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 flex flex-wrap items-center justify-between gap-3 py-3 text-sm">
          <div className="flex flex-wrap items-center gap-2 text-slate-400">
            <ShieldCheck className={ICON.md} />
            分享预览链接
            {work.remain_views != null ? (
              <Badge tone="warning" size="sm" className="ml-1">
                <Eye className={ICON.xs} /> 还可查看 {work.remain_views} 次
              </Badge>
            ) : null}
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Lock className={ICON.xs} /> 已植入数字水印 · 仅供预览
          </div>
        </div>
      </div>

      <header className="border-b border-white/5">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 flex items-center justify-between py-4">
          <BrandLogo variant="consumer" size="sm" to="/" />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
          <div>
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
              <div className="overflow-hidden rounded-2xl border border-white/10">
                <div
                  className="aspect-[16/9] bg-cover bg-center"
                  style={{
                    backgroundImage:
                      'linear-gradient(135deg, rgba(244,183,25,0.25) 0%, rgba(10,22,40,0.95) 55%, #050d18 100%)',
                  }}
                />
              </div>
              <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-gold-500/30 bg-gold-500/10 px-4 py-1.5 text-sm font-medium text-gold-400">
                <Sparkles className="h-4 w-4" />
                精选剧本分享
              </div>
              <h1 className="mt-3 text-3xl font-bold leading-tight md:text-4xl text-white">{work.title}</h1>
              <div className="mt-2 text-sm text-slate-400">
                {work.theme_name || work.theme || '短剧'} · {work.episode_count || '—'} 集 · ScriptForge AI 生成
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-400">
                <UserAvatar name={work.author_nickname || '作者'} size="sm" />
                <span className="font-medium text-white">{work.author_nickname || '匿名作者'}</span>
                <span className="text-slate-600">·</span>
                <Calendar className="h-3.5 w-3.5" />
                {formatDate(work.created_at)}
              </div>
              {work.overall_score != null ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  <Badge tone="gold">
                    <Star className={ICON.xs} /> 评分 {work.overall_score}
                  </Badge>
                </div>
              ) : null}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 }}
              className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-6 md:p-8"
            >
              <div className="relative z-10">
                <div className="mb-6 flex items-center gap-3 border-b border-white/10 pb-4">
                  <FileText className="h-5 w-5 text-gold-400" />
                  <h2 className="text-xl font-bold text-white">作品预览</h2>
                </div>

                <div
                  className="sf-script-rendered prose prose-invert max-w-none prose-headings:text-white prose-p:text-slate-300 prose-strong:text-gold-300"
                  dangerouslySetInnerHTML={{
                    __html: sanitizeHtml(work.rendered_share_html || '<p class="text-slate-500">暂无预览内容</p>'),
                  }}
                />
              </div>
            </motion.div>
          </div>

          <aside className="space-y-4">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-5">
              <h3 className="m-0 mb-3 text-sm font-semibold text-white">分享信息</h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">剩余查看次数</span>
                  <span className="text-white font-medium">{work.remain_views != null ? work.remain_views : '—'}</span>
                </div>
                <div className="flex items-center gap-1.5 text-amber-400">
                  <Lock className={ICON.xs} />
                  已植入数字水印
                </div>
              </div>
              <p className="mt-4 text-[11px] leading-relaxed text-slate-500">
                本作品仅供预览，版权归属原创作者，未经许可不得转载或商用
              </p>
            </div>

            <div className="rounded-2xl border border-gold-500/20 bg-gold-500/5 p-5 text-center">
              <Sparkles className="mx-auto mb-3 h-8 w-8 text-gold-400" />
              <h3 className="text-base font-bold text-white">也想创作爆款剧本？</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">一句话创意，生成完整可拍摄剧本</p>
              <Link to="/register" className="mt-4 block">
                <Button variant="gold" className="w-full" iconRight={<ArrowRight className="w-4 h-4" />}>
                  免费注册
                </Button>
              </Link>
              <Link to="/" className="mt-2 block text-xs text-gold-400 hover:text-gold-300 transition-colors">
                了解更多
              </Link>
            </div>
          </aside>
        </div>

        <div className="mt-12 text-center text-sm text-slate-500">
          <p className="mb-2">本作品由 ScriptForge AI 辅助创作，版权归原创作者所有</p>
          <p>© 2026 ScriptForge · 保留所有权利</p>
        </div>
      </main>
    </div>
  )
}
