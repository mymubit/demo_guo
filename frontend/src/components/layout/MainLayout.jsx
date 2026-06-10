import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'
import {
  Film,
  Menu,
  X,
  User,
  Sparkles,
  Crown,
  FolderKanban,
  UserCircle2,
  LogOut,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

export default function MainLayout() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuthStore()

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20)
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

  const navItems = [
    { path: '/', label: '首页', icon: null },
    { path: '/creation', label: '开始创作', icon: Sparkles },
    { path: '/works', label: '我的作品', icon: FolderKanban },
    { path: '/member', label: '会员中心', icon: Crown },
  ]

  return (
    <div className="min-h-screen flex flex-col">
      {/* 导航栏 */}
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? 'bg-navy-950/90 backdrop-blur-xl border-b border-navy-700/40'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <motion.div
                whileHover={{ rotate: 10, scale: 1.1 }}
                className="w-10 h-10 rounded-xl flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 8px 24px -8px rgba(102, 126, 234, 0.6)',
                }}
              >
                <Film className="w-5 h-5 text-white" />
              </motion.div>
              <span className="text-xl font-bold">
                <span className="gradient-text">ScriptForge</span>
                <span className="text-white/80 ml-1 text-sm font-normal">AI</span>
              </span>
            </Link>

            {/* 桌面导航 */}
            <nav className="hidden md:flex items-center gap-2">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-navy-700/50 text-white'
                        : 'text-navy-200 hover:text-white hover:bg-navy-800/50'
                    }`}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </nav>

            {/* 用户区 */}
            <div className="hidden md:flex items-center gap-4">
              {isAuthenticated ? (
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-navy-800/50 transition-all"
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
                      <span className="text-navy-950 text-sm font-bold">
                        {user?.nickname?.charAt(0) || user?.phone?.slice(-2) || 'U'}
                      </span>
                    </div>
                    <span className="text-sm text-navy-100">
                      {user?.nickname || `用户${user?.phone?.slice(-4) || ''}`}
                    </span>
                  </button>

                  <AnimatePresence>
                    {userMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        className="absolute right-0 top-full mt-2 w-56 py-2 rounded-2xl glass-card shadow-xl"
                      >
                        <Link
                          to="/profile"
                          className="flex items-center gap-3 px-4 py-3 text-navy-100 hover:bg-navy-700/30 transition-all"
                        >
                          <UserCircle2 className="w-4 h-4" />
                          <span>个人中心</span>
                        </Link>
                        <Link
                          to="/works"
                          className="flex items-center gap-3 px-4 py-3 text-navy-100 hover:bg-navy-700/30 transition-all"
                        >
                          <FolderKanban className="w-4 h-4" />
                          <span>我的作品</span>
                        </Link>
                        <Link
                          to="/member"
                          className="flex items-center gap-3 px-4 py-3 text-navy-100 hover:bg-navy-700/30 transition-all"
                        >
                          <Crown className="w-4 h-4 text-gold-400" />
                          <span>会员中心</span>
                        </Link>
                        <div className="border-t border-navy-700/40 my-2" />
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
                    className="px-5 py-2 rounded-xl text-sm font-medium text-navy-100 hover:text-white hover:bg-navy-800/50 transition-all"
                  >
                    登录
                  </Link>
                  <Link
                    to="/register"
                    className="btn-gold px-5 py-2 text-sm !rounded-xl"
                  >
                    免费注册
                  </Link>
                </>
              )}
            </div>

            {/* 移动端菜单按钮 */}
            <button
              className="md:hidden w-10 h-10 flex items-center justify-center rounded-xl bg-navy-800/50 text-white"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* 移动端菜单 */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="md:hidden overflow-hidden bg-navy-950/95 backdrop-blur-xl border-t border-navy-700/40"
            >
              <div className="px-6 py-4 space-y-2">
                {navItems.map((item) => {
                  const isActive = location.pathname === item.path
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`block px-4 py-3 rounded-xl text-sm font-medium ${
                        isActive
                          ? 'bg-navy-700/50 text-white'
                          : 'text-navy-200 hover:text-white hover:bg-navy-800/50'
                      }`}
                    >
                      {item.label}
                    </Link>
                  )
                })}
                <div className="border-t border-navy-700/40 my-3" />
                {isAuthenticated ? (
                  <>
                    <Link
                      to="/profile"
                      className="block px-4 py-3 rounded-xl text-sm text-navy-100 hover:bg-navy-800/50"
                    >
                      个人中心
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-3 rounded-xl text-sm text-red-400 hover:bg-red-500/10"
                    >
                      退出登录
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="block px-4 py-3 rounded-xl text-sm text-navy-100 hover:bg-navy-800/50 text-center"
                    >
                      登录
                    </Link>
                    <Link
                      to="/register"
                      className="block px-4 py-3 rounded-xl text-sm text-center btn-gold !py-3"
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

      {/* 主内容 */}
      <main className="flex-1 pt-20">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* 页脚 */}
      <footer className="border-t border-navy-700/40 bg-navy-950/80">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-2 mb-4">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  }}
                >
                  <Film className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold gradient-text">ScriptForge AI</span>
              </div>
              <p className="text-sm text-navy-300 leading-relaxed">
                基于AI的专业短剧剧本创作平台，将一句话创意转化为完整可拍摄的A级剧本。
              </p>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-4">产品</h4>
              <ul className="space-y-2 text-sm text-navy-300">
                <li><Link to="/creation" className="hover:text-white transition-colors">剧本创作</Link></li>
                <li><Link to="/member" className="hover:text-white transition-colors">会员套餐</Link></li>
                <li><Link to="/" className="hover:text-white transition-colors">功能介绍</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-4">资源</h4>
              <ul className="space-y-2 text-sm text-navy-300">
                <li><Link to="/" className="hover:text-white transition-colors">使用教程</Link></li>
                <li><Link to="/" className="hover:text-white transition-colors">创作指南</Link></li>
                <li><Link to="/" className="hover:text-white transition-colors">常见问题</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-4">联系我们</h4>
              <ul className="space-y-2 text-sm text-navy-300">
                <li>business@scriptforge.ai</li>
                <li>商务合作</li>
                <li>创作者社区</li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-navy-800 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-navy-400">
            <p>© 2026 ScriptForge AI. 保留所有权利。</p>
            <div className="flex items-center gap-6">
              <Link to="/" className="hover:text-white transition-colors">隐私政策</Link>
              <Link to="/" className="hover:text-white transition-colors">服务条款</Link>
              <Link to="/admin" className="hover:text-white transition-colors">管理后台</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
