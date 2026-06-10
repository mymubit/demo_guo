import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import {
  LayoutDashboard,
  Users,
  Crown,
  Settings,
  ShoppingCart,
  LogOut,
  Film,
  ChevronRight,
  Menu,
  X,
  Bell,
  UserCircle2,
  Sparkles,
} from 'lucide-react'

const menuItems = [
  { path: '/admin/dashboard', label: '仪表盘', icon: LayoutDashboard, badge: null },
  { path: '/admin/users', label: '用户管理', icon: Users, badge: '1.2k' },
  { path: '/admin/members', label: '会员管理', icon: Crown, badge: null },
  { path: '/admin/skill-config', label: '技能配置', icon: Settings, badge: null },
  { path: '/admin/orders', label: '订单管理', icon: ShoppingCart, badge: '32' },
]

export default function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const currentItem = menuItems.find((item) => location.pathname.startsWith(item.path))

  const breadcrumb = (() => {
    if (location.pathname === '/admin' || location.pathname.startsWith('/admin/dashboard')) {
      return ['后台管理', '仪表盘']
    }
    if (location.pathname.startsWith('/admin/users')) return ['后台管理', '用户管理']
    if (location.pathname.startsWith('/admin/members')) return ['后台管理', '会员管理']
    if (location.pathname.startsWith('/admin/skill-config')) return ['后台管理', '技能配置']
    if (location.pathname.startsWith('/admin/orders')) return ['后台管理', '订单管理']
    return ['后台管理']
  })()

  function handleLogout() {
    localStorage.removeItem('scriptforge-auth')
    navigate('/admin/login')
  }

  return (
    <div className="min-h-screen bg-navy-950 flex">
      {/* 移动端遮罩 */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 bg-navy-950/80 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* 左侧垂直导航 */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 z-50 transform transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-full bg-gradient-to-b from-navy-900 via-navy-950 to-navy-900 border-r border-navy-700/40 flex flex-col">
          {/* Logo 区 */}
          <div className="p-6 border-b border-navy-700/40">
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 8px 24px -8px rgba(102, 126, 234, 0.6)',
                }}
              >
                <Film className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="font-bold text-white">ScriptForge</div>
                <div className="text-xs text-navy-400">管理后台</div>
              </div>
            </div>
          </div>

          {/* 管理员信息 */}
          <div className="p-4 mx-4 mt-4 rounded-2xl bg-navy-800/40 border border-navy-700/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-950 font-bold text-sm">
                AD
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-white truncate">管理员</div>
                <div className="text-xs text-navy-400">admin@scriptforge.ai</div>
              </div>
              <div className="w-2 h-2 rounded-full bg-green-500" title="在线" />
            </div>
          </div>

          {/* 菜单 */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            <div className="text-xs text-navy-500 uppercase font-semibold px-3 mb-3 tracking-wider">
              主菜单
            </div>
            {menuItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path) ||
                (item.path === '/admin/dashboard' && location.pathname === '/admin')
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-gold-500/20 to-gold-600/10 text-gold-400 border border-gold-500/30 shadow-lg shadow-gold-500/10'
                      : 'text-navy-300 hover:bg-navy-800/50 hover:text-white'
                  }`}
                >
                  <item.icon className={`w-5 h-5 ${isActive ? 'text-gold-400' : ''}`} />
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full ${
                        isActive
                          ? 'bg-gold-500/30 text-gold-400'
                          : 'bg-navy-700/60 text-navy-300'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                  {isActive && <ChevronRight className="w-4 h-4 text-gold-400" />}
                </NavLink>
              )
            })}
          </nav>

          {/* 底部快捷操作 */}
          <div className="p-4 border-t border-navy-700/40">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-purple-600/10 to-gold-500/10 border border-navy-700/30 mb-3">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-gold-400" />
                <span className="text-sm font-semibold text-white">小提示</span>
              </div>
              <p className="text-xs text-navy-300 leading-relaxed">
                所有操作都会被记录，请谨慎进行管理操作。
              </p>
            </div>

            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <LogOut className="w-5 h-5" />
              退出登录
            </button>
          </div>
        </div>
      </aside>

      {/* 右侧内容区 */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* 顶部面包屑 */}
        <header className="sticky top-0 z-30 bg-navy-950/90 backdrop-blur-xl border-b border-navy-700/40">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              {/* 移动端菜单按钮 */}
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-xl text-navy-300 hover:bg-navy-800/50 transition-colors"
              >
                <Menu className="w-6 h-6" />
              </button>

              {/* 面包屑 */}
              <div className="flex items-center gap-2 text-sm">
                {breadcrumb.map((crumb, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    {idx > 0 && <ChevronRight className="w-4 h-4 text-navy-500" />}
                    <span
                      className={
                        idx === breadcrumb.length - 1
                          ? 'text-white font-medium'
                          : 'text-navy-400'
                      }
                    >
                      {crumb}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 右侧操作 */}
            <div className="flex items-center gap-2">
              <button className="relative p-2 rounded-xl text-navy-300 hover:bg-navy-800/50 transition-colors">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
              </button>
              <button
                onClick={handleLogout}
                className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-navy-300 hover:bg-navy-800/50 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>退出</span>
              </button>
            </div>
          </div>
        </header>

        {/* 页面内容 */}
        <main className="flex-1 p-6 lg:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>

        {/* 页脚 */}
        <footer className="px-6 py-4 border-t border-navy-700/40 text-center text-xs text-navy-500">
          © 2026 ScriptForge AI · 管理控制台 · v1.0.0
        </footer>
      </div>
    </div>
  )
}
