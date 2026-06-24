import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'
import {
  Menu,
  X,
  Sparkles,
  Crown,
  Coins,
  FolderKanban,
  UserCircle2,
  LogOut,
  BarChart3,
  Eye,
  ShoppingBag,
  Home,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import WalletBadge from '@/components/billing/WalletBadge'
import BrandLogo from '@/components/ui/BrandLogo'
import UserAvatar from '@/components/ui/UserAvatar'
import ConsumerErrorBoundary from '@/components/shared/ConsumerErrorBoundary'
import { PageContainer } from '@/components/shared/ConsumerSection'
import { ICON } from '@/constants/iconSizes'
import { CONSUMER_TOP_NAV } from '@/config/consumerNav'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const NAV_ICONS = {
  '/': Home,
  '/drama': Sparkles,
  '/evaluate': BarChart3,
  '/pull-sheet': Eye,
  '/works': FolderKanban,
  '/wallet': Coins,
  '/member': Crown,
  '/orders': ShoppingBag,
}

export default function MainLayout() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuthStore()

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 8)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    setMobileMenuOpen(false)
    setUserMenuOpen(false)
  }, [location.pathname])

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const navItems = CONSUMER_TOP_NAV.map((item) => ({
    ...item,
    icon: NAV_ICONS[item.path] ?? null,
  }))

  return (
    <div className="min-h-screen flex flex-col bg-navy-950">
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? 'bg-navy-950/90 backdrop-blur-xl border-b border-white/10 shadow-lg shadow-black/20'
            : 'bg-navy-950/60 backdrop-blur-lg border-b border-white/5'
        }`}
      >
        <PageContainer width="7xl" className="py-3">
          <div className="flex items-center justify-between">
            <BrandLogo variant="consumer" size="sm" to="/" />

            <nav className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-gold-500/15 text-gold-300'
                        : 'text-slate-300 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </nav>

            <div className="hidden lg:flex items-center gap-3">
              {isAuthenticated && <WalletBadge compact />}
              {isAuthenticated ? (
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-all"
                  >
                    <UserAvatar src={user?.avatar} name={user?.nickname} phone={user?.phone} size="sm" />
                    <span className="text-sm text-slate-200">
                      {user?.nickname || `用户${user?.phone?.slice(-4) || ''}`}
                    </span>
                  </button>

                  <AnimatePresence>
                    {userMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-white/10 bg-navy-900/95 backdrop-blur-xl py-2 shadow-xl shadow-black/40"
                      >
                        <Link
                          to="/profile"
                          className="flex items-center gap-3 px-4 py-3 text-slate-200 hover:bg-white/5 transition-all"
                        >
                          <UserCircle2 className={ICON.md} />
                          <span>个人中心</span>
                        </Link>
                        <Link
                          to="/works"
                          className="flex items-center gap-3 px-4 py-3 text-slate-200 hover:bg-white/5 transition-all"
                        >
                          <FolderKanban className="w-4 h-4" />
                          <span>我的作品</span>
                        </Link>
                        <Link
                          to="/wallet"
                          className="flex items-center gap-3 px-4 py-3 text-slate-200 hover:bg-white/5 transition-all"
                        >
                          <Coins className="w-4 h-4 text-gold-400" />
                          <span>充值创作币</span>
                        </Link>
                        <Link
                          to="/member"
                          className="flex items-center gap-3 px-4 py-3 text-slate-200 hover:bg-white/5 transition-all"
                        >
                          <Crown className="w-4 h-4 text-gold-400" />
                          <span>会员中心</span>
                        </Link>
                        <Link
                          to="/orders"
                          className="flex items-center gap-3 px-4 py-3 text-slate-200 hover:bg-white/5 transition-all"
                        >
                          <ShoppingBag className="w-4 h-4 text-gold-400" />
                          <span>我的订单</span>
                        </Link>
                        <div className="border-t border-white/10 my-2" />
                        <button
                          onClick={handleLogout}
                          className="flex items-center gap-3 px-4 py-3 w-full text-left text-red-400 hover:bg-red-500/10 transition-all"
                        >
                          <LogOut className="w-4 h-4" />
                          <span>退出登录</span>
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="px-5 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-all"
                  >
                    登录
                  </Link>
                  <Link
                    to="/register"
                    className="inline-flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold bg-gradient-to-r from-gold-300 to-gold-500 text-navy-950 shadow-gold hover:from-gold-200 hover:to-gold-400 hover:-translate-y-0.5 transition-all"
                  >
                    免费注册
                  </Link>
                </>
              )}
            </div>

            <button
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-slate-200 lg:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </PageContainer>

        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="lg:hidden overflow-hidden bg-navy-950/95 backdrop-blur-xl border-t border-white/10"
            >
              <div className="px-6 py-4 space-y-2">
                {navItems.map((item) => {
                  const isActive = location.pathname === item.path
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium ${
                        isActive
                          ? 'bg-gold-500/15 text-gold-300'
                          : 'text-slate-300 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      {renderLucideIcon(item.icon, ICON.md)}
                      {item.label}
                    </Link>
                  )
                })}
                <div className="border-t border-white/10 my-3" />
                {isAuthenticated ? (
                  <>
                    <Link
                      to="/profile"
                      className="block px-4 py-3 rounded-lg text-sm text-slate-200 hover:bg-white/5"
                    >
                      个人中心
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-3 rounded-lg text-sm text-red-400 hover:bg-red-500/10"
                    >
                      退出登录
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="block px-4 py-3 rounded-lg text-sm text-slate-200 hover:bg-white/5 text-center"
                    >
                      登录
                    </Link>
                    <Link
                      to="/register"
                      className="block px-4 py-3 rounded-lg text-sm text-center font-semibold bg-gradient-to-r from-gold-300 to-gold-500 text-navy-950"
                    >
                      免费注册
                    </Link>
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.header>

      <main className="flex-1 pt-[4.25rem]">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.3 }}
          >
            <ConsumerErrorBoundary>
              <Outlet />
            </ConsumerErrorBoundary>
          </motion.div>
        </AnimatePresence>
      </main>

      <footer className="border-t border-white/10 bg-navy-950/80 backdrop-blur-sm">
        <PageContainer width="7xl" className="py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="font-semibold text-white mb-4">产品</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><Link to="/drama" className="hover:text-gold-300 transition-colors">剧本创作</Link></li>
                <li><Link to="/evaluate" className="hover:text-gold-300 transition-colors">剧本评估</Link></li>
                <li><Link to="/pull-sheet" className="hover:text-gold-300 transition-colors">拉片分析</Link></li>
                <li><Link to="/works" className="hover:text-gold-300 transition-colors">我的作品</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-4">账户</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><Link to="/member" className="hover:text-gold-300 transition-colors">会员套餐</Link></li>
                <li><Link to="/wallet" className="hover:text-gold-300 transition-colors">创作币充值</Link></li>
                <li><Link to="/orders" className="hover:text-gold-300 transition-colors">我的订单</Link></li>
                <li><Link to="/profile" className="hover:text-gold-300 transition-colors">个人中心</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-4">Drama Skills</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li className="text-slate-500">12位专业角色协作</li>
                <li className="text-slate-500">8阶段创作流程</li>
                <li className="text-slate-500">AI驱动的剧本工厂</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-4">联系我们</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>business@scriptforge.ai</li>
                <li className="text-slate-500">商务合作</li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-slate-500">
            <p>© 2026 ScriptForge AI. 保留所有权利。</p>
            <div className="flex items-center gap-6">
              <span className="text-slate-600">隐私政策</span>
              <span className="text-slate-600">服务条款</span>
              <Link to="/admin" className="hover:text-slate-300 transition-colors">管理后台</Link>
            </div>
          </div>
        </PageContainer>
      </footer>
    </div>
  )
}
