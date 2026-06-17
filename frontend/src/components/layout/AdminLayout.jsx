import { Outlet, NavLink, useLocation, useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useMemo, useState } from 'react'
import { LogOut, Menu, ChevronRight, ChevronDown } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import {
  ADMIN_NAV_GROUPS,
  findAdminNavItem,
  getAdminBreadcrumb,
  isAdminNavItemActive,
} from '@/config/adminNav'
import BrandLogo from '@/components/ui/BrandLogo'
import AdminErrorBoundary from '@/components/admin/AdminErrorBoundary'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const COLLAPSE_STORAGE_KEY = 'admin-nav-collapsed-v2'

function readCollapsedState() {
  try {
    const raw = localStorage.getItem(COLLAPSE_STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function writeCollapsedState(state) {
  try {
    localStorage.setItem(COLLAPSE_STORAGE_KEY, JSON.stringify(state))
  } catch {
    /* ignore */
  }
}

function NavItem({ item, active, onNavigate }) {
  return (
    <NavLink
      to={item.path}
      onClick={onNavigate}
      title={item.description || item.label}
      className={`group relative flex items-center gap-3.5 rounded-xl px-3.5 py-3 text-base leading-snug transition-all ${
        active
          ? 'bg-gold-500/16 text-gold-50 font-semibold shadow-sm shadow-gold-500/10'
          : 'text-navy-200 hover:bg-white/[0.06] hover:text-white font-medium'
      }`}
    >
      {active ? (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-7 rounded-full bg-gradient-to-b from-gold-300 to-gold-500" />
      ) : null}
      {renderLucideIcon(
        item.icon,
        `w-[22px] h-[22px] shrink-0 transition-colors ${
          active ? 'text-gold-400' : 'text-navy-400 group-hover:text-navy-100'
        }`,
      )}
      <span className="truncate tracking-wide">{item.label}</span>
    </NavLink>
  )
}

export default function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(() => readCollapsedState())

  const breadcrumb = useMemo(
    () => getAdminBreadcrumb(location.pathname, location.search),
    [location.pathname, location.search]
  )

  const activeGroupId = useMemo(() => {
    const item = findAdminNavItem(location.pathname, location.search)
    return item?.groupId || ''
  }, [location.pathname, location.search])

  useEffect(() => {
    if (!activeGroupId) return
    const group = ADMIN_NAV_GROUPS.find((g) => g.id === activeGroupId)
    if (group?.collapsible && collapsed[group.id]) {
      setCollapsed((prev) => {
        const next = { ...prev, [group.id]: false }
        writeCollapsedState(next)
        return next
      })
    }
  }, [activeGroupId]) // eslint-disable-line react-hooks/exhaustive-deps

  function toggleGroup(groupId) {
    setCollapsed((prev) => {
      const next = { ...prev, [groupId]: !prev[groupId] }
      writeCollapsedState(next)
      return next
    })
  }

  function handleLogout() {
    logout()
    navigate('/admin/login')
  }

  const adminName = user?.nickname || '管理员'
  const adminInitials = adminName.slice(0, 2).toUpperCase()
  const closeSidebar = () => setSidebarOpen(false)

  return (
    <div className="min-h-screen bg-navy-950 flex">
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeSidebar}
            className="fixed inset-0 bg-navy-950/80 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      <aside
        className={`fixed top-0 left-0 h-full w-72 z-50 transform transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-full bg-gradient-to-b from-navy-900 via-navy-950 to-navy-950 border-r border-white/5 flex flex-col shadow-xl shadow-black/20">
          <div className="px-5 pt-6 pb-5 border-b border-white/10">
            <Link to="/admin" className="flex items-center gap-4 group">
              <BrandLogo variant="admin" size="lg" showText={false} to={null} interactive={false} />
              <div className="min-w-0">
                <div className="text-xl font-bold gradient-text leading-tight tracking-tight">
                  ScriptForge
                </div>
                <div className="text-[15px] text-navy-400 mt-1 tracking-wide">运营控制台</div>
              </div>
            </Link>
            <div className="mt-5 flex min-w-0 items-center gap-3.5 rounded-2xl border border-white/5 bg-slate-900/40 px-4 py-3">
              <div className="w-11 h-11 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-950 font-bold text-sm shrink-0 shadow-md shadow-gold-500/20">
                {adminInitials}
              </div>
              <div className="min-w-0">
                <div className="text-base font-semibold text-white truncate">{adminName}</div>
                <div className="text-[15px] text-navy-400 truncate">运营账号</div>
              </div>
            </div>
          </div>

          <nav className="flex-1 px-4 py-5 overflow-y-auto space-y-6">
            {ADMIN_NAV_GROUPS.map((group) => {
              const isCollapsible = Boolean(group.collapsible)
              const isExpanded = isCollapsible ? !collapsed[group.id] : true
              const groupHasActive = group.items.some((item) =>
                isAdminNavItemActive(location.pathname, item, location.search)
              )

              return (
                <div key={group.id}>
                  {isCollapsible ? (
                    <button
                      type="button"
                      onClick={() => toggleGroup(group.id)}
                      className={`w-full flex items-center justify-between px-2.5 py-2 mb-2 text-[15px] font-semibold tracking-wide transition-colors ${
                        groupHasActive ? 'text-gold-400' : 'text-navy-400 hover:text-navy-200'
                      }`}
                    >
                      <span>{group.label}</span>
                      <ChevronDown
                        className={`w-4 h-4 opacity-70 transition-transform ${isExpanded ? '' : '-rotate-90'}`}
                      />
                    </button>
                  ) : (
                    <div
                      className={`px-2.5 py-2 mb-2 text-[15px] font-semibold tracking-wide ${
                        groupHasActive ? 'text-navy-300' : 'text-navy-400'
                      }`}
                    >
                      {group.label}
                    </div>
                  )}
                  {isExpanded ? (
                    <div className="space-y-1.5">
                      {group.items.map((item) => (
                        <NavItem
                          key={item.id}
                          item={item}
                          active={isAdminNavItemActive(location.pathname, item, location.search)}
                          onNavigate={closeSidebar}
                        />
                      ))}
                    </div>
                  ) : null}
                </div>
              )
            })}
          </nav>

          <div className="p-4 border-t border-white/10">
            <button
              type="button"
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-3.5 py-3 rounded-xl text-base text-navy-400 hover:text-red-400 hover:bg-red-500/5 transition-colors"
            >
              <LogOut className="w-5 h-5" />
              退出登录
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 lg:ml-72 flex flex-col min-h-screen">
        <header className="sticky top-0 z-30 bg-navy-950/95 backdrop-blur-xl border-b border-white/10">
          <div className="flex items-center justify-between px-8 py-4">
            <div className="flex items-center gap-3 min-w-0">
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-lg text-navy-300 hover:bg-white/[0.06]"
              >
                <Menu className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-2.5 text-base min-w-0 flex-wrap">
                {breadcrumb.map((crumb, idx) => (
                  <div key={`${crumb}-${idx}`} className="flex items-center gap-2.5 min-w-0">
                    {idx > 0 && <ChevronRight className="w-4 h-4 text-navy-500 shrink-0" />}
                    <span
                      className={
                        idx === breadcrumb.length - 1
                          ? 'text-white font-semibold text-[17px] truncate'
                          : 'text-navy-400 truncate'
                      }
                    >
                      {crumb}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="hidden sm:inline-flex items-center gap-2.5 px-5 py-2.5 rounded-xl text-base text-navy-400 hover:bg-white/[0.06]"
            >
              <LogOut className="w-4 h-4" />
              退出
            </button>
          </div>
        </header>

        <main className="flex-1 min-w-0 w-full bg-gradient-to-b from-[#0a0e1a] to-[#0e1424] p-6 lg:p-9">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
            >
              <AdminErrorBoundary>
                <Outlet />
              </AdminErrorBoundary>
            </motion.div>
          </AnimatePresence>
        </main>

        <footer className="px-8 py-3 border-t border-white/5 text-center text-sm text-navy-400">
          ScriptForge 管理后台
        </footer>
      </div>
    </div>
  )
}
