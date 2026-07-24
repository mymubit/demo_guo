# Review Package W0 Task 5

## frontend\src\App.tsx

import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/auth/AuthContext'
import { V3Routes } from '@/app/router'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 15_000, refetchOnWindowFocus: false, retry: false },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <V3Routes />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}


## frontend\src\app\router.tsx

import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '@/router/ProtectedRoute'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ModelsPage } from '@/pages/ModelsPage'
import { LogsPage } from '@/pages/LogsPage'
import { SystemPage } from '@/pages/SystemPage'
import { BillingPage } from '@/pages/BillingPage'
import { ProjectOverviewPage } from '@/pages/ProjectOverviewPage'
import { AppShell } from './AppShell'

/** V3 全局一级导航路径（不含项目内路由） */
export const V3_NAV_PATHS = [
  '/dashboard',
  '/models',
  '/logs',
  '/system',
  '/billing',
] as const

export function V3Routes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/system" element={<SystemPage />} />
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/projects/:id" element={<ProjectOverviewPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}


## frontend\src\app\AppShell.tsx

import { useState, type ComponentType } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Clapperboard,
  CreditCard,
  LayoutDashboard,
  LogOut,
  Menu,
  ScrollText,
  Settings2,
  Sparkles,
  X,
} from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'

type NavItem = {
  to: string
  label: string
  hint: string
  icon: ComponentType<{ className?: string }>
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: '创作仪表盘', hint: '项目与创作进度', icon: LayoutDashboard },
  { to: '/models', label: '模型配置', hint: '供应商与运行参数', icon: Sparkles },
  { to: '/logs', label: '执行日志', hint: '生成与调用记录', icon: ScrollText },
  { to: '/system', label: '系统配置', hint: '工作空间偏好', icon: Settings2 },
  { to: '/billing', label: '套餐', hint: '方案与用量', icon: CreditCard },
]

function Navigation({ onNavigate }: { onNavigate: () => void }) {
  return (
    <nav className="space-y-1 px-3 py-5" aria-label="主导航">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/dashboard'}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'group flex items-center gap-3 rounded-md px-3 py-3 transition',
              isActive ? 'bg-[#e9f3ef] text-[#0f5c4b]' : 'text-slate-600 hover:bg-slate-100',
            )
          }
        >
          <span className="grid h-8 w-8 place-items-center rounded-md bg-slate-100 group-hover:bg-white">
            <item.icon className="h-4 w-4" />
          </span>
          <span>
            <span className="block text-sm font-semibold">{item.label}</span>
            <span className="mt-0.5 block text-[11px] text-slate-400">{item.hint}</span>
          </span>
        </NavLink>
      ))}
    </nav>
  )
}

export function AppShell() {
  const [open, setOpen] = useState(false)
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  const sidebar = (
    <aside className="flex h-full flex-col bg-white text-slate-900">
      <div className="flex h-[76px] items-center gap-3 border-b border-slate-200 px-5">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#0f5c4b] text-white">
          <Clapperboard className="h-4 w-4" />
        </div>
        <div>
          <div className="text-[15px] font-bold tracking-tight">ScriptForge</div>
          <div className="mt-0.5 text-[10px] font-medium uppercase tracking-[.16em] text-slate-400">
            创作工作台 · V3
          </div>
        </div>
      </div>
      <Navigation onNavigate={() => setOpen(false)} />
      <div className="mt-auto border-t border-slate-200 p-4">
        <div className="mb-3 truncate px-2 text-xs text-slate-500">
          {auth?.user?.nickname || auth?.user?.username || '当前用户'}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2 text-slate-500"
          onClick={() => void handleLogout()}
          iconLeft={<LogOut className="h-4 w-4" />}
        >
          退出登录
        </Button>
      </div>
    </aside>
  )

  return (
    <div className="flex h-dvh min-h-[600px] bg-[#f6f8f7] text-slate-900">
      <aside className="hidden w-[252px] shrink-0 border-r border-slate-200 lg:block">{sidebar}</aside>
      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-slate-900/30"
            aria-label="关闭菜单遮罩"
            onClick={() => setOpen(false)}
          />
          <aside className="relative h-full w-[280px] shadow-xl">
            {sidebar}
            <button
              type="button"
              className="absolute right-4 top-5 text-slate-500"
              onClick={() => setOpen(false)}
              title="关闭"
            >
              <X className="h-5 w-5" />
            </button>
          </aside>
        </div>
      ) : null}
      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-[68px] shrink-0 items-center border-b border-slate-200 bg-white px-4 sm:px-8">
          <button
            type="button"
            className="lg:hidden"
            onClick={() => setOpen(true)}
            title="打开菜单"
          >
            <Menu className="h-5 w-5" />
          </button>
        </header>
        <main className="min-h-0 flex-1 overflow-auto">
          <Outlet />
        </main>
      </section>
    </div>
  )
}


## frontend\src\app\router.test.tsx

import { describe, expect, it } from 'vitest'
import { V3_NAV_PATHS } from './router'

describe('v3 router paths', () => {
  it('exposes product IA paths and not studio', () => {
    expect(V3_NAV_PATHS).toEqual(
      expect.arrayContaining(['/dashboard', '/models', '/logs', '/system', '/billing']),
    )
    expect(V3_NAV_PATHS.some((p) => p.startsWith('/studio'))).toBe(false)
  })
})


## frontend\src\pages\DashboardPage.tsx

import { PageShell } from '@/components/layout/PageShell'

export function DashboardPage() {
  return (
    <PageShell title="创作仪表盘" description="管理你的短剧项目与创作进度。">
      <p className="text-sm text-ink-muted">占位页：后续接入项目列表与新建入口。</p>
    </PageShell>
  )
}


## frontend\src\pages\LoginPage.tsx

import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Clapperboard, LockKeyhole } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth(); const navigate = useNavigate(); const [username, setUsername] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(false)
  useEffect(() => { if (isAuthenticated) navigate('/dashboard', { replace: true }) }, [isAuthenticated, navigate])
  async function submit(event: FormEvent) { event.preventDefault(); setLoading(true); setError(null); try { await login(username.trim(), password); navigate('/dashboard', { replace: true }) } catch (err) { setError(err instanceof Error ? err.message : String(err)) } finally { setLoading(false) } }
  return <div className="grid min-h-dvh bg-[#f4f5f2] lg:grid-cols-[minmax(360px,42%)_1fr]"><aside className="hidden flex-col justify-between bg-[#171918] p-10 text-white lg:flex"><div><div className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center bg-[#d7ff45] text-[#171918]"><Clapperboard className="h-4 w-4" /></div><div><div className="text-sm font-semibold">ScriptForge</div><div className="text-[10px] uppercase tracking-[.18em] text-zinc-500">Studio V6</div></div></div><div className="mt-24 max-w-xs"><div className="font-mono text-[10px] uppercase tracking-[.18em] text-zinc-500">Operation graph / trace ledger / artifact versions</div><h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight">进入你的<br /><span className="text-[#d7ff45]">创作控制面</span></h1></div></div><div className="flex items-center gap-2 text-xs text-zinc-500"><span className="h-2 w-2 bg-[#d7ff45]" />V6 runtime ready</div></aside><main className="flex items-center justify-center p-5 sm:p-10"><div className="w-full max-w-[420px]"><div className="mb-8 flex items-center gap-3 lg:hidden"><div className="grid h-9 w-9 place-items-center bg-[#1b1d1c] text-[#d7ff45]"><Clapperboard className="h-4 w-4" /></div><div><div className="text-sm font-semibold">ScriptForge</div><div className="text-[10px] uppercase tracking-[.16em] text-zinc-500">Studio V6</div></div></div><form onSubmit={submit} className="border border-black/10 bg-white p-6 shadow-[0_18px_55px_rgba(21,25,22,.08)] sm:p-8"><div className="flex h-10 w-10 items-center justify-center bg-[#eef3dc] text-[#6f8c12]"><LockKeyhole className="h-4 w-4" /></div><h2 className="mt-6 text-2xl font-semibold">登录 Studio</h2><p className="mt-2 text-sm text-zinc-500">使用工作空间账号继续。</p>{error ? <div className="mt-5 border border-red-200 bg-red-50 p-3 text-xs text-red-800">{error}</div> : null}<label className="mt-7 block text-xs font-medium">账号<input id="username" required autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} className="mt-2 h-11 w-full border border-black/15 px-3 text-sm outline-none focus:border-[#89aa22]" placeholder="用户名" /></label><label className="mt-4 block text-xs font-medium">密码<input id="password" required type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} className="mt-2 h-11 w-full border border-black/15 px-3 text-sm outline-none focus:border-[#89aa22]" /></label><button disabled={loading} className="mt-6 flex h-11 w-full items-center justify-between bg-[#1b1d1c] px-4 text-sm font-semibold text-white disabled:opacity-50">{loading ? '验证中…' : '进入控制面'}<ArrowRight className="h-4 w-4 text-[#d7ff45]" /></button></form></div></main></div>
}

