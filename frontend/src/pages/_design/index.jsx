/**
 * index.jsx — 设计稿预览总览
 *
 * 提供一个顶部分段切换器（前台 / 后台）+ 侧边锚点导航，
 * 让一份设计稿能像 DESIGN_PROTOTYPE.html 那样在一个页面内完整预览。
 *
 * 路由：/preview
 */
import { useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, LayoutDashboard, FolderKanban } from 'lucide-react'
import { cn } from '@/utils/cn'

const CONSUMER_NAV = [
  { to: '/preview/home', label: '首页 Hero' },
  { to: '/preview/creation', label: '创作工作台' },
  { to: '/preview/works', label: '作品库' },
  { to: '/preview/works/p-10248', label: '作品详情' },
  { to: '/preview/member', label: '会员中心' },
  { to: '/preview/wallet', label: '钱包 / 创作币' },
  { to: '/preview/recharge', label: '充值' },
  { to: '/preview/orders', label: '我的订单' },
  { to: '/preview/tools', label: '工具（评估/拉片）' },
  { to: '/preview/profile', label: '个人中心' },
  { to: '/preview/auth', label: '登录 / 注册' },
  { to: '/preview/share/abc123', label: '分享落地页' },
]

const ADMIN_NAV = [
  { to: '/preview/admin/dashboard', label: '仪表盘' },
  { to: '/preview/admin/projects', label: '创作项目监控' },
  { to: '/preview/admin/users', label: '用户管理' },
  { to: '/preview/admin/orders', label: '订单管理' },
  { to: '/preview/admin/members', label: '会员 / 套餐' },
  { to: '/preview/admin/billing', label: '充值 / 创作币' },
  { to: '/preview/admin/quality', label: '质量缺陷' },
  { to: '/preview/admin/skills', label: '技能中心' },
  { to: '/preview/admin/mainchain', label: '主链工作室' },
  { to: '/preview/admin/agent', label: 'Agent 中心' },
  { to: '/preview/admin/models', label: '模型中心' },
  { to: '/preview/admin/portal', label: '门户内容' },
  { to: '/preview/admin/orchestration', label: '调度监控' },
  { to: '/preview/admin/system', label: '系统设置' },
]

export default function DesignIndex() {
  const location = useLocation()
  // 简单从路径判断当前分段
  const isAdmin = location.pathname.includes('/admin')
  const [stage, setStage] = useState(isAdmin ? 'admin' : 'consumer')

  const items = stage === 'admin' ? ADMIN_NAV : CONSUMER_NAV

  return (
    <div className="min-h-screen bg-navy-950 text-white">
      {/* 顶部 — 阶段切换器 */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-navy-950/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1280px] items-center gap-3 px-5 py-2.5 text-xs">
          <div className="flex items-center gap-2">
            <span className="grid h-3.5 w-3.5 place-items-center rounded bg-gradient-to-br from-gold-300 to-gold-500" />
            <b className="font-bold tracking-wider">ScriptForge Design</b>
          </div>
          <div className="ml-4 flex gap-1 rounded-full bg-white/5 p-[3px]">
            <StageBtn active={stage === 'consumer'} onClick={() => setStage('consumer')}>
              <Sparkles className="h-3 w-3" /> 前台 · C 端
            </StageBtn>
            <StageBtn active={stage === 'admin'} onClick={() => setStage('admin')}>
              <LayoutDashboard className="h-3 w-3" /> 后台 · Console
            </StageBtn>
          </div>
          <div className="ml-auto flex items-center gap-3 text-slate-500">
            <span>来源</span>
            <code className="rounded bg-white/5 px-2 py-0.5 font-mono text-[11px] text-slate-300">
              docs/DESIGN_PROTOTYPE.html
            </code>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-[1280px] gap-6 px-5 py-6">
        {/* 侧栏 — 锚点导航 */}
        <aside className="sticky top-16 h-fit w-44 shrink-0">
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-3">
            <div className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              {stage === 'admin' ? '后台页面' : '前台页面'}
            </div>
            <nav className="space-y-0.5">
              {items.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-[13px] transition-colors',
                      isActive
                        ? 'bg-white/10 text-white'
                        : 'text-slate-400 hover:bg-white/5 hover:text-white',
                    )
                  }
                >
                  {n.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="mt-3 rounded-2xl border border-dashed border-indigo-500/35 bg-indigo-500/[0.08] p-3 text-[12px] text-slate-300">
            <b className="text-indigo-300">路由前缀</b>
            <div className="mt-1 font-mono text-[11px] text-slate-400">
              {stage === 'admin' ? '/preview/admin/*' : '/preview/*'}
            </div>
          </div>
        </aside>

        {/* 主体 */}
        <main className="min-w-0 flex-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.18 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}

function StageBtn({ active, children, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 font-medium transition-colors',
        active ? 'bg-white/10 text-white' : 'text-slate-300 hover:text-white',
      )}
    >
      {children}
    </button>
  )
}
