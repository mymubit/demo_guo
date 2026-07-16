import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  Clapperboard,
  Cpu,
  FolderKanban,
  LogOut,
  Settings2,
  FileSearch,
} from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { useRecentProjects } from '@/hooks/useRecentProjects'
import { cn } from '@/utils/cn'
import { Button } from '@/components/ui/Button'
import { PC_MIN_WIDTH } from '@/config/workbench'

const navItems = [
  { to: '/projects', label: '项目', icon: FolderKanban, end: true },
  { to: '/tools/script-review', label: '外部评测', icon: FileSearch },
  { to: '/admin/model', label: '模型管理', icon: Cpu },
  { to: '/admin/config', label: '技能覆盖', icon: Settings2 },
]

function projectIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/projects\/([^/]+)\/(workbench|settings)/)
  return match?.[1] ?? null
}

export function AppShell() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const recent = useRecentProjects(1)
  const latest = recent[0] ?? null
  const routeProjectId = projectIdFromPath(location.pathname)

  const onLatestWorkbench =
    Boolean(latest) &&
    Boolean(routeProjectId) &&
    routeProjectId === latest?.id &&
    location.pathname.includes('/workbench')

  return (
    <div
      className="flex h-dvh min-h-[720px] min-w-pc bg-canvas"
      style={{ minWidth: PC_MIN_WIDTH }}
    >
      <aside className="flex w-[clamp(10rem,14vw,14rem)] shrink-0 flex-col border-r border-navy-800 bg-navy-900 text-slate-200">
        <div className="flex items-center gap-2 border-b border-white/10 px-5 py-5">
          <Clapperboard className="h-5 w-5 text-gold-400" />
          <div>
            <div className="text-sm font-semibold tracking-wide text-white">ScriptForge</div>
            <div className="text-[11px] text-slate-400">短剧创作工作台</div>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition',
                  isActive
                    ? 'bg-white/10 text-white ring-1 ring-gold-400/30'
                    : 'text-slate-300 hover:bg-white/5 hover:text-white',
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </NavLink>
          ))}

          {latest ? (
            <div className="mt-3 border-t border-white/10 pt-3">
              <div className="mb-1.5 px-3 text-[11px] font-medium tracking-wide text-slate-500">
                最近项目
              </div>
              <NavLink
                to={`/projects/${latest.id}/workbench`}
                title={latest.title}
                className={cn(
                  'flex items-start gap-2 rounded-lg px-3 py-2 text-sm transition',
                  onLatestWorkbench
                    ? 'bg-gold-400/15 text-white ring-1 ring-gold-400/40'
                    : 'text-slate-300 hover:bg-white/5 hover:text-white',
                )}
              >
                <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold-400" />
                <span className="min-w-0">
                  <span className="block truncate font-medium">{latest.title}</span>
                  <span className="mt-0.5 block text-[11px] text-slate-500">回工作台</span>
                </span>
              </NavLink>
            </div>
          ) : null}
        </nav>
        <div className="border-t border-white/10 p-3">
          <div className="mb-2 truncate px-2 text-xs text-slate-400">
            {auth?.user?.nickname || auth?.user?.username || '已登录'}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-slate-300 hover:bg-white/5 hover:text-white"
            iconLeft={<LogOut className="h-3.5 w-3.5" />}
            onClick={async () => {
              await logout()
              navigate('/login')
            }}
          >
            退出
          </Button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
