import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Home, ArrowLeft, Film, Compass, Search, AlertTriangle, Crown, BarChart3, Eye } from 'lucide-react'
import { pageEnter } from '@/constants/motion'
import { renderLucideIcon } from '@/utils/renderLucideIcon'
import { Button } from '@/components/ui'
import { CONSUMER_TOP_NAV } from '@/config/consumerNav'

const SUGGESTION_ICONS = {
  '/': Home,
  '/drama': Film,
  '/evaluate': BarChart3,
  '/pull-sheet': Eye,
  '/works': Film,
  '/member': Crown,
}

const SUGGESTIONS = CONSUMER_TOP_NAV.filter((item) =>
  ['/', '/drama', '/evaluate', '/pull-sheet', '/works', '/member'].includes(item.path),
).map((item) => ({
  name: item.label,
  icon: SUGGESTION_ICONS[item.path] || Film,
  path: item.path,
}))

export default function NotFound() {
  return (
    <motion.div
      {...pageEnter}
      className="flex min-h-[calc(100vh-4.25rem)] items-center justify-center bg-navy-950 bg-radial-glow px-6 py-16"
    >
      <div className="w-full max-w-2xl text-center">
        <div className="relative mb-8 inline-block">
          <div className="mx-auto grid h-24 w-24 place-items-center rounded-2xl border border-white/10 bg-white/[0.04]">
            <Compass className="h-12 w-12 text-gold-400" />
          </div>
        </div>

        <h1 className="mb-4 text-7xl font-bold md:text-8xl">
          <span className="sf-text-gradient-gold">404</span>
        </h1>
        <h2 className="mb-4 text-2xl font-bold text-white md:text-3xl">页面不存在</h2>
        <p className="mx-auto mb-10 max-w-md text-lg leading-relaxed text-slate-400">
          很抱歉，你访问的页面可能已经被删除、重命名或暂时不可用。让我们帮你回到正确的轨道。
        </p>

        <div className="mb-12 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link to="/">
            <Button variant="gold" size="lg" iconLeft={<Home className="h-5 w-5" />}>
              返回首页
            </Button>
          </Link>
          <Button
            variant="secondary"
            size="lg"
            iconLeft={<ArrowLeft className="h-5 w-5" />}
            onClick={() => window.history.back()}
          >
            上一页
          </Button>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-sm p-6 md:p-8">
          <h3 className="mb-5 flex items-center justify-center gap-2 font-semibold text-white">
            <Search className="h-4 w-4 text-gold-400" />
            你可能想访问
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-6">
            {SUGGESTIONS.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="group rounded-xl border border-white/10 bg-white/5 p-4 transition-all hover:border-gold-500/30 hover:bg-gold-500/10"
              >
                {renderLucideIcon(item.icon, 'mx-auto mb-2 h-5 w-5 text-slate-500 transition-colors group-hover:text-gold-400')}
                <span className="text-sm text-slate-400 transition-colors group-hover:text-white">
                  {item.name}
                </span>
              </Link>
            ))}
          </div>
        </div>

        <p className="mt-10 flex items-center justify-center gap-2 text-sm text-slate-500">
          <AlertTriangle className="h-4 w-4" />
          如果你认为这是一个错误，请联系管理员或稍后再试
        </p>
      </div>
    </motion.div>
  )
}
