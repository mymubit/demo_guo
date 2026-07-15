import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Clapperboard, FolderKanban, LogOut, Settings2, FileSearch } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { cn } from '@/utils/cn'
import { Button } from '@/components/ui/Button'
import { PC_MIN_WIDTH } from '@/config/workbench'

const navItems = [
  { to: '/projects', label: '项目', icon: FolderKanban },
  { to: '/tools/script-review', label: '外部评测', icon: FileSearch },
  { to: '/admin/config', label: '配置后台', icon: Settings2 },
]

export function AppShell() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div
      className="flex h-dvh min-h-[720px] min-w-pc bg-canvas"
      style={{ minWidth: PC_MIN_WIDTH }}
    >
      <aside className="flex w-[clamp(10rem,14vw,14rem)] shrink-0 flex-col bg-navy-900 text-slate-200">
        <div className="flex items-center gap-2 border-b border-white/10 px-5 py-5">
          <Clapperboard className="h-5 w-5 text-gold-400" />
          <div>
            <div className="text-sm font-semibold tracking-wide text-white">ScriptForge</div>
            <div className="text-[11px] text-slate-400">短剧创作工作台</div>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition',
                  isActive ? 'bg-white/10 text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/10 p-3">
          <div className="mb-2 truncate px-2 text-xs text-slate-400">
            {auth?.user?.nickname || auth?.user?.phone || '已登录'}
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
