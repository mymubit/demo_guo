/**
 * 工具页共享布局 — 左导航 / 右工作区（浅色 dashboard）
 */
import { NavLink } from 'react-router-dom'
import { BarChart3, Eye } from 'lucide-react'
import { cn } from '@/utils/cn'
import { PageContainer } from '@/components/shared/ConsumerSection'
import { ICON } from '@/constants/iconSizes'
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
    desc: '粘贴分镜或链接，拆解镜头与节奏',
    icon: Eye,
    to: '/pull-sheet',
  },
]

export default function ToolsShell({ active, title, subtitle, children }) {
  return (
    <motion.div
      {...pageEnter}
      className="relative z-10 grid min-h-[calc(100vh-4.25rem)] grid-cols-1 lg:grid-cols-[280px_1fr]"
    >
      <aside className="border-r border-gray-200 bg-white p-5">
        <div className="text-xs font-semibold uppercase tracking-wider text-gray-400">专业工具</div>
        <nav className="mt-3 space-y-1.5">
          {TOOLS.map((t) => {
            const isActive = active === t.key
            return (
              <NavLink
                key={t.key}
                to={t.to}
                className={cn(
                  'flex w-full items-start gap-3 rounded-xl border p-3 text-left transition-colors',
                  isActive
                    ? 'border-brand-200 bg-brand-50 text-brand-800'
                    : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50',
                )}
              >
                {renderLucideIcon(t.icon, cn(ICON.md, 'mt-0.5 shrink-0', isActive ? 'text-brand-600' : 'text-gray-400'))}
                <div>
                  <div className="text-sm font-semibold">{t.label}</div>
                  <div className="mt-0.5 text-[11px] text-gray-400">{t.desc}</div>
                </div>
              </NavLink>
            )
          })}
        </nav>
        <div className="mt-5 rounded-xl border border-dashed border-brand-200 bg-brand-50/50 p-3 text-[12px] text-gray-600">
          <b className="text-brand-700">提示</b>
          <p className="mt-1 text-gray-500">评估结果会入库质量缺陷，帮助主链团队迭代技能模板。</p>
        </div>
      </aside>

      <main className="min-w-0 overflow-auto bg-gray-50 p-6 md:p-7 lg:p-9">
        <PageContainer width="5xl" className="px-0">
          {(title || subtitle) && (
            <header className="mb-6">
              {title ? <h1 className="text-2xl font-bold text-gray-900">{title}</h1> : null}
              {subtitle ? <p className="mt-1 text-sm text-gray-500">{subtitle}</p> : null}
            </header>
          )}
          {children}
        </PageContainer>
      </main>
    </motion.div>
  )
}
