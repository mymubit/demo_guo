import { motion } from 'framer-motion'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Film,
  User,
  Lock,
  Eye,
  EyeOff,
  LogIn,
  Shield,
  ArrowRight,
  AlertCircle,
} from 'lucide-react'

export default function AdminLogin() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!form.username || !form.password) {
      setError('请输入用户名和密码')
      return
    }

    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      localStorage.setItem('scriptforge-auth', JSON.stringify({ is_staff: true, username: form.username }))
      navigate('/admin/dashboard')
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-navy-950 via-navy-900 to-navy-950 flex items-center justify-center px-6 relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 rounded-full bg-purple-600/20 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 rounded-full bg-gold-500/15 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <motion.div
            whileHover={{ scale: 1.05, rotate: 5 }}
            className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              boxShadow: '0 10px 40px -10px rgba(102, 126, 234, 0.6)',
            }}
          >
            <Film className="w-8 h-8 text-white" />
          </motion.div>
          <h1 className="text-2xl font-bold text-white mb-1">ScriptForge 管理后台</h1>
          <p className="text-navy-300 text-sm">请使用管理员账号登录</p>
        </div>

        {/* 登录卡片 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="glass-card rounded-3xl p-8"
        >
          <div className="flex items-center gap-3 mb-6 px-4 py-3 rounded-xl bg-gold-500/10 border border-gold-500/30">
            <Shield className="w-5 h-5 text-gold-400 flex-shrink-0" />
            <span className="text-sm text-gold-400">
              安全通道 · 所有操作将被记录
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 错误提示 */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-3"
              >
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </motion.div>
            )}

            {/* 用户名 */}
            <div>
              <label className="block text-sm font-medium text-navy-200 mb-2">用户名</label>
              <div className="relative">
                <User className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  placeholder="请输入管理员用户名"
                  className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white placeholder:text-navy-500 focus:outline-none focus:border-gold-500/60 transition-colors"
                  autoComplete="username"
                />
              </div>
            </div>

            {/* 密码 */}
            <div>
              <label className="block text-sm font-medium text-navy-200 mb-2">密码</label>
              <div className="relative">
                <Lock className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="请输入密码"
                  className="w-full pl-12 pr-12 py-3.5 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white placeholder:text-navy-500 focus:outline-none focus:border-gold-500/60 transition-colors"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-navy-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* 登录按钮 */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 font-semibold text-base hover:shadow-lg hover:shadow-gold-500/30 transition-all flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-5 h-5 border-2 border-navy-950/30 border-t-navy-950 rounded-full"
                  />
                  登录中...
                </>
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  登录管理后台
                </>
              )}
            </button>
          </form>

          {/* 底部链接 */}
          <div className="mt-6 pt-6 border-t border-navy-700/40 flex items-center justify-between text-sm">
            <Link to="/" className="text-navy-400 hover:text-white transition-colors flex items-center gap-1">
              <ArrowRight className="w-4 h-4 rotate-180" />
              返回主站
            </Link>
            <Link to="/" className="text-gold-400 hover:text-gold-300 transition-colors">
              忘记密码？
            </Link>
          </div>
        </motion.div>

        <p className="text-center text-xs text-navy-500 mt-6">
          © 2026 ScriptForge AI · 管理控制台 · 仅供授权人员访问
        </p>
      </motion.div>
    </div>
  )
}
