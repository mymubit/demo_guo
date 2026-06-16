import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Phone, Lock, Eye, EyeOff, LogIn, Shield, ArrowRight, AlertCircle } from 'lucide-react'
import BrandLogo from '@/components/ui/BrandLogo'
import { auth } from '@/services/api'
import { useAuthStore } from '@/store/authStore'

export default function AdminLogin() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login: setAuth } = useAuthStore()
  const [form, setForm] = useState({ phone: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (location.state?.error) {
      setError(location.state.error)
    }
  }, [location.state])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!/^1[3-9]\d{9}$/.test(form.phone)) {
      setError('请输入有效的 11 位手机号')
      return
    }
    if (!form.password || form.password.length < 8) {
      setError('密码至少 8 位')
      return
    }
    setLoading(true)
    try {
      const data = await auth.login(form)
      const user = data.user || {}
      if (!user.is_staff && !user.is_superuser) {
        setError('该账号无后台管理权限')
        return
      }
      setAuth(user, data.access, data.refresh)
      toast.success('欢迎回来，管理员')
      navigate('/admin/dashboard', { replace: true })
    } catch (err) {
      setError(err.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="mb-8 text-center">
          <BrandLogo variant="admin" size="lg" to={null} showText={false} className="mb-4 justify-center" />
          <h1 className="mb-1 text-2xl font-bold text-white">ScriptForge 管理后台</h1>
          <p className="text-sm text-slate-400">使用管理员手机号登录（需 is_staff 权限）</p>
        </div>

        <div className="sf-console-panel rounded-3xl p-8">
          <div className="flex items-center gap-3 mb-6 px-4 py-3 rounded-xl bg-gold-500/10 border border-gold-500/30">
            <Shield className="w-5 h-5 text-gold-400 flex-shrink-0" />
            <span className="text-sm text-gold-400">独立管理控制台 · 非 Django Admin</span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-3">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-navy-200 mb-2">管理员手机号</label>
              <div className="relative">
                <Phone className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type="tel"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  placeholder="11 位手机号"
                  className="sf-control pl-12"
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-navy-200 mb-2">密码</label>
              <div className="relative">
                <Lock className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="请输入密码"
                  className="sf-control pl-12 pr-12"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-navy-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 font-semibold flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? '登录中…' : (<><LogIn className="w-5 h-5" />登录管理后台</>)}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-white/5">
            <Link to="/" className="text-navy-400 hover:text-white text-sm flex items-center gap-1">
              <ArrowRight className="w-4 h-4 rotate-180" />
              返回主站
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
