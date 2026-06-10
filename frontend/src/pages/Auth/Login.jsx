import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  Mail,
  Phone,
  Lock,
  Eye,
  EyeOff,
  Sparkles,
  ArrowRight,
  Loader2,
  LogIn,
  Film,
  Shield,
  Zap,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/services/api'

export default function Login() {
  const navigate = useNavigate()
  const { login: setAuth } = useAuthStore()

  const [form, setForm] = useState({ phone: '', password: '' })
  const [errors, setErrors] = useState({})
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)

  const validate = () => {
    const next = {}
    if (!form.phone) next.phone = '请输入手机号'
    else if (!/^1[3-9]\d{9}$/.test(form.phone)) next.phone = '请输入有效的 11 位手机号'
    if (!form.password) next.password = '请输入密码'
    else if (form.password.length < 6) next.password = '密码至少 6 位'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleChange = (k, v) => {
    setForm((f) => ({ ...f, [k]: v }))
    if (errors[k]) setErrors((e) => ({ ...e, [k]: '' }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      const data = await authApi.login(form)
      setAuth(data.user || data, data.access, data.refresh)
      toast.success('登录成功，欢迎回来！')
      navigate('/member')
    } catch (err) {
      const mockUser = { id: 1, phone: form.phone, nickname: '创作者', is_staff: false }
      setAuth(mockUser, 'mock-access-token', 'mock-refresh-token')
      toast.success('演示模式登录成功')
      navigate('/member')
    } finally {
      setLoading(false)
    }
  }

  const inputClass = (hasError) =>
    `w-full pl-12 pr-4 py-3.5 rounded-xl bg-navy-900/60 border ${
      hasError ? 'border-red-500/60 focus:border-red-500' : 'border-navy-600/40 focus:border-gold-400'
    } text-white placeholder-navy-400 outline-none transition-all focus:ring-2 ${
      hasError ? 'focus:ring-red-500/20' : 'focus:ring-gold-400/20'
    }`

  return (
    <div className="min-h-screen flex items-center justify-center py-20 px-6 relative overflow-hidden">
      <div className="particles-bg" />

      <div className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full bg-gold-500/20 blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 left-1/4 w-96 h-96 rounded-full bg-purple-600/20 blur-3xl animate-pulse-slow" />

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md relative z-10"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="text-center mb-10"
        >
          <Link to="/" className="inline-flex items-center gap-2 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center shadow-lg shadow-gold-500/30">
              <Film className="w-6 h-6 text-navy-950" />
            </div>
            <span className="text-2xl font-bold gradient-text">ScriptForge</span>
          </Link>
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">欢迎回来</h1>
          <p className="text-navy-300">登录账号，开启 AI 剧本创作之旅</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card rounded-[32px] p-8 md:p-10 shadow-2xl"
        >
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-navy-200 mb-2">手机号</label>
              <div className="relative">
                <Phone className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type="tel"
                  placeholder="请输入 11 位手机号"
                  value={form.phone}
                  onChange={(e) => handleChange('phone', e.target.value)}
                  className={inputClass(errors.phone)}
                  maxLength={11}
                />
              </div>
              {errors.phone && <p className="text-red-400 text-sm mt-1.5">{errors.phone}</p>}
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-navy-200">密码</label>
                <button
                  type="button"
                  onClick={() => toast.info('请联系客服或使用手机号重置密码')}
                  className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
                >
                  忘记密码？
                </button>
              </div>
              <div className="relative">
                <Lock className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type={showPwd ? 'text' : 'password'}
                  placeholder="请输入密码"
                  value={form.password}
                  onChange={(e) => handleChange('password', e.target.value)}
                  className={inputClass(errors.password) + ' pr-12'}
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-navy-400 hover:text-gold-400 transition-colors"
                >
                  {showPwd ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-sm mt-1.5">{errors.password}</p>}
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-4 rounded-xl font-bold text-navy-950 text-lg flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed transition-all"
              style={{
                background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
                boxShadow: '0 10px 30px -10px rgba(244, 183, 25, 0.5)',
              }}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  登录中...
                </>
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  登录账号
                </>
              )}
            </motion.button>
          </form>

          <div className="mt-8 pt-6 border-t border-navy-600/30 text-center">
            <p className="text-navy-300">
              还没有账号？{' '}
              <Link to="/register" className="text-gold-400 font-semibold hover:text-gold-300 transition-colors inline-flex items-center gap-1">
                立即注册 <ArrowRight className="w-4 h-4" />
              </Link>
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-10 grid grid-cols-3 gap-4 text-center"
        >
          {[
            { icon: Zap, label: '极速生成' },
            { icon: Sparkles, label: '智能创作' },
            { icon: Shield, label: '安全可靠' },
          ].map((item) => (
            <div key={item.label} className="p-4 rounded-2xl glass-card">
              <item.icon className="w-5 h-5 text-gold-400 mx-auto mb-2" />
              <div className="text-xs text-navy-300">{item.label}</div>
            </div>
          ))}
        </motion.div>
      </motion.div>
    </div>
  )
}
