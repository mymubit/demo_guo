import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Home, ArrowLeft, Film, Compass, Search, AlertTriangle } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-navy-950 via-navy-900 to-navy-950 flex items-center justify-center px-6 relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-purple-600/10 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-gold-500/10 blur-3xl" />
      </div>

      <div className="relative z-10 max-w-2xl w-full text-center">
        {/* 图标 */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="relative inline-block mb-8"
        >
          <motion.div
            animate={{ rotate: [0, 5, -5, 5, 0] }}
            transition={{ duration: 3, repeat: Infinity, repeatDelay: 2 }}
            className="w-28 h-28 rounded-3xl mx-auto flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
              border: '1px solid rgba(102, 126, 234, 0.3)',
            }}
          >
            <Compass className="w-14 h-14 text-purple-400" />
          </motion.div>
        </motion.div>

        {/* 404 文字 */}
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.6 }}
        >
          <h1 className="text-8xl md:text-9xl font-bold mb-4">
            <span className="gradient-text">404</span>
          </h1>
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
            页面不存在
          </h2>
          <p className="text-navy-300 text-lg mb-10 max-w-md mx-auto leading-relaxed">
            很抱歉，你访问的页面可能已经被删除、重命名或暂时不可用。
            让我们帮你回到正确的轨道。
          </p>
        </motion.div>

        {/* 按钮组 */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
        >
          <Link
            to="/"
            className="btn-gold text-base inline-flex items-center gap-2 !py-4 !px-8"
          >
            <Home className="w-5 h-5" />
            返回首页
          </Link>
          <Link
            to="/"
            onClick={(e) => {
              e.preventDefault()
              window.history.back()
            }}
            className="btn-ghost text-base inline-flex items-center gap-2 !py-4 !px-8"
          >
            <ArrowLeft className="w-5 h-5" />
            上一页
          </Link>
        </motion.div>

        {/* 建议链接 */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="glass-card rounded-3xl p-6 md:p-8"
        >
          <h3 className="text-white font-semibold mb-5 flex items-center justify-center gap-2">
            <Search className="w-4 h-4 text-gold-400" />
            你可能想访问
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { name: '首页', icon: Home, path: '/' },
              { name: '开始创作', icon: Film, path: '/creation' },
              { name: '我的作品', icon: Film, path: '/works' },
              { name: '会员中心', icon: Film, path: '/member' },
            ].map((item, idx) => (
              <Link
                key={idx}
                to={item.path}
                className="p-4 rounded-xl bg-navy-800/50 hover:bg-navy-700/50 border border-navy-700/30 hover:border-gold-500/40 transition-all group"
              >
                <item.icon className="w-5 h-5 text-navy-300 group-hover:text-gold-400 transition-colors mx-auto mb-2" />
                <span className="text-sm text-navy-200 group-hover:text-white transition-colors">
                  {item.name}
                </span>
              </Link>
            ))}
          </div>
        </motion.div>

        {/* 底部提示 */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-10 text-sm text-navy-500 flex items-center justify-center gap-2"
        >
          <AlertTriangle className="w-4 h-4" />
          如果你认为这是一个错误，请联系管理员或稍后再试
        </motion.p>
      </div>
    </div>
  )
}
