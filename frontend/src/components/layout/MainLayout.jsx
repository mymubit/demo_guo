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

  const navIcons = {
    '/': null,
    '/creation': Sparkles,
    '/evaluate': BarChart3,
    '/pull-sheet': Eye,
    '/works': FolderKanban,
    '/wallet': Coins,
    '/member': Crown,
    '/orders': ShoppingBag,
  }

  const navItems = CONSUMER_TOP_NAV.map((item) => ({
    ...item,
    icon: navIcons[item.path] ?? null,
  }))

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? 'bg-white/95 backdrop-blur-xl border-b border-gray-200 shadow-sm'
            : 'bg-white border-b border-gray-100'
        }`}
      >
        <PageContainer width="7xl" className="py-3">
          <div className="flex items-center justify-between">
            <BrandLogo variant="consumer" size="sm" to="/" />

            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-brand-50 text-brand-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </nav>

            <div className="hidden md:flex items-center gap-3">
              {isAuthenticated && <WalletBadge compact />}
              {isAuthenticated ? (
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all"
                  >
                    <UserAvatar src={user?.avatar} name={user?.nickname} phone={user?.phone} size="sm" />
                    <span className="text-sm text-gray-700">
                      {user?.nickname || `用户${user?.phone?.slice(-4) || ''}`}
                    </span>
                  </button>

                  <AnimatePresence>
                    {userMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-gray-200 bg-white py-2 shadow-lg"
                      >
                        <Link
                          to="/profile"
                          className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-50 transition-all"
                        >
                          <UserCircle2 className={ICON.md} />
                          <span>个人中心</span>
                        </Link>
                        <Link
                          to="/works"
                          className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-50 transition-all"
                        >
                          <FolderKanban className="w-4 h-4" />
                          <span>我的作品</span>
                        </Link>
                        <Link
                          to="/wallet"
                          className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-50 transition-all"
                        >
                          <Coins className="w-4 h-4 text-accent-500" />
                          <span>充值创作币</span>
                        </Link>
                        <Link
                          to="/member"
                          className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-50 transition-all"
                        >
                          <Crown className="w-4 h-4 text-accent-500" />
                          <span>会员中心</span>
                        </Link>
                        <Link
                          to="/orders"
                          className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-50 transition-all"
                        >
                          <ShoppingBag className="w-4 h-4 text-accent-500" />
                          <span>我的订单</span>
                        </Link>
                        <div className="border-t border-gray-100 my-2" />
                        <button
                          onClick={handleLogout}
                          className="flex items-center gap-3 px-4 py-3 w-full text-left text-red-600 hover:bg-red-50 transition-all"
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
                    className="px-5 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-all"
                  >
                    登录
                  </Link>
                  <Link
                    to="/register"
                    className="btn-gold px-5 py-2 text-sm !rounded-lg"
                  >
                    免费注册
                  </Link>
                </>
              )}
            </div>

            <button
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-700 md:hidden"
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
              className="md:hidden overflow-hidden bg-white border-t border-gray-100"
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
                          ? 'bg-brand-50 text-brand-700'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }`}
                    >
                      {renderLucideIcon(item.icon, ICON.md)}
                      {item.label}
                    </Link>
                  )
                })}
                <div className="border-t border-gray-100 my-3" />
                {isAuthenticated ? (
                  <>
                    <Link
                      to="/profile"
                      className="block px-4 py-3 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
                    >
                      个人中心
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-3 rounded-lg text-sm text-red-600 hover:bg-red-50"
                    >
                      退出登录
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="block px-4 py-3 rounded-lg text-sm text-gray-700 hover:bg-gray-50 text-center"
                    >
                      登录
                    </Link>
                    <Link
                      to="/register"
                      className="block px-4 py-3 rounded-lg text-sm text-center btn-gold !py-3"
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
            transition={{ duration: 0.25 }}
          >
            <ConsumerErrorBoundary>
              <Outlet />
            </ConsumerErrorBoundary>
          </motion.div>
        </AnimatePresence>
      </main>

      <footer className="border-t border-gray-200 bg-white">
        <PageContainer width="7xl" className="py-12">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-8 mb-8">
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">产品</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><Link to="/creation" className="hover:text-gray-900 transition-colors">剧本创作</Link></li>
                <li><Link to="/evaluate" className="hover:text-gray-900 transition-colors">剧本评估</Link></li>
                <li><Link to="/pull-sheet" className="hover:text-gray-900 transition-colors">拉片分析</Link></li>
                <li><Link to="/works" className="hover:text-gray-900 transition-colors">我的作品</Link></li>
                <li><Link to="/member" className="hover:text-gray-900 transition-colors">会员套餐</Link></li>
                <li><Link to="/wallet" className="hover:text-gray-900 transition-colors">创作币充值</Link></li>
                <li><Link to="/orders" className="hover:text-gray-900 transition-colors">我的订单</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-4">资源</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><Link to="/" className="hover:text-gray-900 transition-colors">使用教程</Link></li>
                <li><Link to="/" className="hover:text-gray-900 transition-colors">创作指南</Link></li>
                <li><Link to="/" className="hover:text-gray-900 transition-colors">常见问题</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-4">联系我们</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li>business@scriptforge.ai</li>
                <li>商务合作</li>
                <li>创作者社区</li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-gray-100 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-gray-400">
            <p>© 2026 ScriptForge AI. 保留所有权利。</p>
            <div className="flex items-center gap-6">
              <Link to="/" className="hover:text-gray-700 transition-colors">隐私政策</Link>
              <Link to="/" className="hover:text-gray-700 transition-colors">服务条款</Link>
              <Link to="/admin" className="hover:text-gray-700 transition-colors">管理后台</Link>
            </div>
          </div>
        </PageContainer>
      </footer>
    </div>
  )
}
