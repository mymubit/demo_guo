import { NavLink } from 'react-router-dom'
import { BarChart3, Eye } from 'lucide-react'
import { cn } from '@/utils/cn'
import { renderLucideIcon } from '@/utils/renderLucideIcon'
import { pageEnter } from '@/constants/motion'
import { motion } from 'framer-motion'

const TOOLS = [
  {
    key: 'evaluate',
    label: '剧本评估',
    desc: '已完成作品四维评分与改进建议',
    icon: BarChart3,
    to: '/evaluate',
  },
  {
    key: 'pullsheet',
    label: '拉片分析',
    desc: '粘贴参考作品，拆解节奏与钩子',
    icon: Eye,
    to: '/pull-sheet',
  },
]

export default function ToolsShell({ active, title, subtitle, children }) {
  return (
    <motion.div
      {...pageEnter}
      className="relative z-10 grid min-h-[calc(100vh-4.25rem)] grid-cols-1 lg:grid-cols-[280px_1fr] bg-navy-950"
    >
      <aside className="border-r border-white/10 bg-white/[0.02] backdrop-blur-sm p-5">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">专业工具</div>
        <nav className="mt-3 space-y-1.5">
          {TOOLS.map((t) => {
            const isActive = active === t.key
            return (
              <NavLink
                key={t.key}
                to={t.to}
                className={cn(
                  'flex w-full items-start gap-3 rounded-xl border p-3 text-left transition-all',
                  isActive
                    ? 'border-gold-500/30 bg-gold-500/10 text-white'
                    : 'border-white/5 bg-white/[0.02] text-slate-400 hover:border-white/10 hover:bg-white/[0.05] hover:text-slate-200',
                )}
              >
                {renderLucideIcon(t.icon, cn('w-5 h-5 mt-0.5 shrink-0', isActive ? 'text-gold-400' : 'text-slate-500'))}
                <div>
                  <div className="text-sm font-semibold">{t.label}</div>
                  <div className={cn('mt-0.5 text-[11px]', isActive ? 'text-gold-300/70' : 'text-slate-500')}>{t.desc}</div>
                </div>
              </NavLink>
            )
          })}
        </nav>
        <div className="mt-5 rounded-xl border border-dashed border-gold-500/20 bg-gold-500/5 p-3 text-[12px] text-slate-400">
          <b className="text-gold-400">提示</b>
          <p className="mt-1 text-slate-500">评估结果会帮助主链团队迭代技能模板，持续提升生成质量。</p>
        </div>
      </aside>

      <main className="min-w-0 overflow-auto p-6 md:p-7 lg:p-9">
        <div className="max-w-4xl mx-auto">
          {(title || subtitle) && (
            <header className="mb-6">
              {title ? <h1 className="text-2xl font-bold text-white">{title}</h1> : null}
              {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
            </header>
          )}
          {children}
        </div>
      </main>
    </motion.div>
  )
}
