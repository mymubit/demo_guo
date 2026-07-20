import { useEffect, useMemo, useState, type ComponentType } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  ChevronDown,
  Clapperboard,
  ClipboardList,
  Cpu,
  FolderKanban,
  LogOut,
  ScrollText,
  Settings2,
  FileSearch,
  Wrench,
} from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { useRecentProjects } from '@/hooks/useRecentProjects'
import { cn } from '@/utils/cn'
import { Button } from '@/components/ui/Button'
import { PC_MIN_WIDTH } from '@/config/workbench'

type NavItem = {
  to: string
  label: string
  icon: ComponentType<{ className?: string }>
  end?: boolean
  /** 覆盖默认 active 判断（如日志/链路同页多路由） */
  match?: (pathname: string) => boolean
}

type NavGroup = {
  id: string
  label: string
  items: NavItem[]
  /** 是否默认可折叠；运维默认折叠 */
  collapsible?: boolean
}

const NAV_GROUPS: NavGroup[] = [
  {
    id: 'create',
    label: '创作',
    items: [{ to: '/projects', label: '项目', icon: FolderKanban, end: true }],
  },
  {
    id: 'tools',
    label: '评测工具',
    items: [
      { to: '/tools/script-review', label: '外部评测', icon: FileSearch, end: true },
      { to: '/tools/script-review/records', label: '评审记录', icon: ClipboardList },
    ],
  },
  {
    id: 'ops',
    label: '运维',
    collapsible: true,
    items: [
      { to: '/admin/model', label: '模型管理', icon: Cpu },
      {
        to: '/admin/llm/logs',
        label: 'LLM 调用',
        icon: ScrollText,
        match: (pathname) => pathname.startsWith('/admin/llm/'),
      },
      { to: '/admin/config', label: '技能覆盖', icon: Settings2 },
      { to: '/admin/skill-ops', label: '技能运维', icon: Wrench },
    ],
  },
]

const OPS_OPEN_KEY = 'sf.nav.opsOpen'

function projectIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/projects\/([^/]+)\/(workbench|settings)/)
  return match?.[1] ?? null
}

function pathInGroup(pathname: string, group: NavGroup): boolean {
  return group.items.some((item) => {
    if (item.match?.(pathname)) return true
    return item.end ? pathname === item.to : pathname === item.to || pathname.startsWith(`${item.to}/`)
  })
}

function NavItemLink({ item }: { item: NavItem }) {
  const Icon = item.icon
  const location = useLocation()
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) => {
        const active = item.match ? item.match(location.pathname) : isActive
        return cn(
          'group relative flex items-center gap-2.5 rounded-md px-3 py-2.5 text-sm transition',
          active
            ? 'bg-shell-accent/20 font-medium text-white'
            : 'text-shell-muted hover:bg-white/5 hover:text-white',
        )
      }}
    >
      {({ isActive }) => {
        const active = item.match ? item.match(location.pathname) : isActive
        return (
          <>
            <span
              className={cn(
                'absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-shell-accent transition',
                active ? 'opacity-100' : 'opacity-0',
              )}
            />
            <Icon
              className={cn('h-4 w-4 shrink-0', active ? 'text-shell-accent' : 'text-shell-muted')}
            />
            {item.label}
          </>
        )
      }}
    </NavLink>
  )
}

export function AppShell() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const recent = useRecentProjects(1)
  const latest = recent[0] ?? null
  const routeProjectId = projectIdFromPath(location.pathname)

  const opsActive = useMemo(
    () => pathInGroup(location.pathname, NAV_GROUPS.find((g) => g.id === 'ops')!),
    [location.pathname],
  )

  const [opsOpen, setOpsOpen] = useState(() => {
    if (typeof window === 'undefined') return false
    const saved = window.localStorage.getItem(OPS_OPEN_KEY)
    if (saved === '1') return true
    if (saved === '0') return false
    return false
  })

  useEffect(() => {
    if (opsActive) setOpsOpen(true)
  }, [opsActive])

  useEffect(() => {
    window.localStorage.setItem(OPS_OPEN_KEY, opsOpen ? '1' : '0')
  }, [opsOpen])

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
      <aside className="relative flex w-[clamp(13rem,16vw,16.5rem)] shrink-0 flex-col bg-shell text-shell-ink">
        <div className="absolute inset-y-0 right-0 w-px bg-gradient-to-b from-shell-accent/50 via-white/10 to-transparent" />
        <div className="border-b border-white/10 px-4 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-shell-accent/15 ring-1 ring-shell-accent/35">
              <Clapperboard className="h-4 w-4 text-shell-accent" />
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold tracking-wide text-white">
                ScriptForge
              </div>
              <div className="text-[11px] text-shell-muted">影棚工台</div>
            </div>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-5 overflow-y-auto px-2 py-4">
          {NAV_GROUPS.map((group) => {
            const isOps = group.collapsible
            const open = !isOps || opsOpen || opsActive
            return (
              <div key={group.id}>
                {isOps ? (
                  <button
                    type="button"
                    onClick={() => setOpsOpen((v) => !v)}
                    className="mb-1.5 flex w-full items-center justify-between px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-shell-muted hover:text-shell-ink"
                  >
                    <span>{group.label}</span>
                    <ChevronDown
                      className={cn('h-3.5 w-3.5 transition', open ? 'rotate-0' : '-rotate-90')}
                    />
                  </button>
                ) : (
                  <div className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-shell-muted">
                    {group.label}
                  </div>
                )}
                {open ? (
                  <div className="flex flex-col gap-0.5">
                    {group.items.map((item) => (
                      <NavItemLink key={item.to} item={item} />
                    ))}
                  </div>
                ) : null}
              </div>
            )
          })}

          {latest ? (
            <div className="mt-auto border-t border-white/10 pt-4">
              <div className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-shell-muted">
                最近项目
              </div>
              <NavLink
                to={`/projects/${latest.id}/workbench`}
                title={latest.title}
                className={cn(
                  'flex items-start gap-2 rounded-md px-3 py-2.5 text-sm transition',
                  onLatestWorkbench
                    ? 'bg-shell-accent/20 text-white'
                    : 'text-shell-muted hover:bg-white/5 hover:text-white',
                )}
              >
                <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-shell-accent" />
                <span className="min-w-0">
                  <span className="block truncate font-medium">{latest.title}</span>
                  <span className="mt-0.5 block text-[11px] text-shell-muted">回工作台</span>
                </span>
              </NavLink>
            </div>
          ) : null}
        </nav>

        <div className="border-t border-white/10 p-3">
          <div className="mb-2 truncate px-2 text-xs text-shell-muted">
            {auth?.user?.nickname || auth?.user?.username || '已登录'}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-shell-muted hover:bg-white/5 hover:text-white"
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
