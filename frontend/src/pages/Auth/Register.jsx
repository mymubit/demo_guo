import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  Phone,
  Lock,
  Eye,
  EyeOff,
  User,
  ArrowRight,
  Loader2,
  UserPlus,
  Sparkles,
  Check,
  AlertCircle,
} from 'lucide-react'
import BrandLogo from '@/components/ui/BrandLogo'
import { useAuthStore } from '@/store/authStore'
import { auth } from '@/services/api'

export default function Register() {
  const navigate = useNavigate()
  const { login: setAuth } = useAuthStore()

  const [form, setForm] = useState({ phone: '', password: '', confirmPassword: '', nickname: '' })
  const [errors, setErrors] = useState({})
  const [showPwd, setShowPwd] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)

  const passwordStrength = (() => {
    const pwd = form.password
    if (!pwd) return { level: 0, label: '', color: '' }
    let score = 0
    if (pwd.length >= 8) score++
    if (/[A-Z]/.test(pwd)) score++
    if (/[0-9]/.test(pwd)) score++
    if (/[^A-Za-z0-9]/.test(pwd)) score++
    const levels = [
      { label: '弱', color: 'bg-red-500' },
      { label: '一般', color: 'bg-orange-500' },
      { label: '良好', color: 'bg-yellow-500' },
      { label: '强', color: 'bg-gold-500' },
      { label: '非常强', color: 'bg-green-500' },
    ]
    return { level: score, ...levels[Math.max(0, score - 1)] }
  })()

  const validate = () => {
    const next = {}
    if (!form.phone) next.phone = '请输入手机号'
    else if (!/^1[3-9]\d{9}$/.test(form.phone)) next.phone = '请输入有效的 11 位手机号'
    if (!form.password) next.password = '请输入密码'
    else if (form.password.length < 8) next.password = '密码至少 8 位'
    if (!form.confirmPassword) next.confirmPassword = '请确认密码'
    else if (form.confirmPassword !== form.password) next.confirmPassword = '两次输入的密码不一致'
    if (form.nickname && form.nickname.length > 20) next.nickname = '昵称最多 20 个字符'
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
    const payload = {
      phone: form.phone,
      password: form.password,
      password_confirm: form.confirmPassword,
    }
    if (form.nickname) payload.nickname = form.nickname
    try {
      const data = await auth.register(payload)
      setAuth(data.user, data.access, data.refresh)
      toast.success('注册成功，欢迎加入 ScriptForge！')
      navigate('/member')
    } catch (err) {
      toast.error(err.message || '注册失败，请稍后重试')
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

      <div className="absolute top-1/3 left-1/4 w-96 h-96 rounded-full bg-purple-600/20 blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/3 right-1/4 w-96 h-96 rounded-full bg-gold-500/20 blur-3xl animate-pulse-slow" />

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
          <BrandLogo variant="consumer" size="md" to="/" className="justify-center mb-4" />
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">创建新账号</h1>
          <p className="text-navy-300">只需几步，立即体验 AI 剧本创作</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card rounded-[32px] p-8 md:p-10 shadow-2xl"
        >
          <form onSubmit={handleSubmit} className="space-y-4.5">
            <div>
              <label className="block text-sm font-medium text-navy-200 mb-2">手机号</label>
              <div className="relative">
                <Phone className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type="tel"
                  placeholder="请输入 11 位手机号"
                  value={form.phone}
                  onChange={(e) => handleChange('phone', e.target.value.replace(/\D/g, ''))}
                  className={inputClass(errors.phone)}
                  maxLength={11}
                />
              </div>
              {errors.phone && <p className="text-red-400 text-sm mt-1.5">{errors.phone}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-navy-200 mb-2">
                密码 <span className="text-navy-400 font-normal">(至少 6 位)</span>
              </label>
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
              {form.password && (
                <div className="mt-2 flex items-center gap-3">
                  <div className="flex-1 h-1.5 rounded-full bg-navy-800 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${passwordStrength.color}`}
                      style={{ width: `${(passwordStrength.level / 4) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-navy-300 w-12 text-right">{passwordStrength.label}</span>
                </div>
              )}
              {errors.password && <p className="text-red-400 text-sm mt-1.5">{errors.password}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-navy-200 mb-2">确认密码</label>
              <div className="relative">
                <Lock className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type={showConfirm ? 'text' : 'password'}
                  placeholder="请再次输入密码"
                  value={form.confirmPassword}
                  onChange={(e) => handleChange('confirmPassword', e.target.value)}
                  className={inputClass(errors.confirmPassword) + ' pr-12'}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-navy-400 hover:text-gold-400 transition-colors"
                >
                  {showConfirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {form.confirmPassword && form.confirmPassword === form.password && (
                <div className="mt-1.5 flex items-center gap-1.5 text-sm text-green-400">
                  <Check className="w-4 h-4" /> 两次密码输入一致
                </div>
              )}
              {errors.confirmPassword && <p className="text-red-400 text-sm mt-1.5">{errors.confirmPassword}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-navy-200 mb-2">
                昵称 <span className="text-navy-400 font-normal">(可选)</span>
              </label>
              <div className="relative">
                <User className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="给自己起一个好听的名字"
                  value={form.nickname}
                  onChange={(e) => handleChange('nickname', e.target.value)}
                  className={inputClass(errors.nickname)}
                  maxLength={20}
                />
              </div>
              {errors.nickname && <p className="text-red-400 text-sm mt-1.5">{errors.nickname}</p>}
            </div>

            <div className="pt-2 flex items-start gap-2 text-xs text-navy-300">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-gold-400" />
              <span>
                注册即表示您同意我们的
                <Link to="#" className="text-gold-400 hover:text-gold-300 mx-0.5">服务条款</Link>
                和
                <Link to="#" className="text-gold-400 hover:text-gold-300 mx-0.5">隐私政策</Link>
              </span>
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
                  创建账号中...
                </>
              ) : (
                <>
                  <UserPlus className="w-5 h-5" />
                  立即注册
                </>
              )}
            </motion.button>
          </form>

          <div className="mt-7 pt-5 border-t border-navy-600/30 text-center">
            <p className="text-navy-300">
              已有账号？{' '}
              <Link to="/login" className="text-gold-400 font-semibold hover:text-gold-300 transition-colors inline-flex items-center gap-1">
                立即登录 <ArrowRight className="w-4 h-4" />
              </Link>
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-8 p-5 rounded-2xl glass-card-gold"
        >
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-gold-400 flex-shrink-0" />
            <div className="text-sm text-navy-200">
              <span className="font-semibold text-white">新用户专享：</span>
              注册即送 3 次免费剧本创作体验，立即开始你的创作之旅！
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}
