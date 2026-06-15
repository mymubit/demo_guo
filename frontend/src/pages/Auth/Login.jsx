import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  Phone,
  Lock,
  Eye,
  EyeOff,
  Sparkles,
  ArrowRight,
  LogIn,
  Shield,
  Zap,
} from 'lucide-react'
import BrandLogo from '@/components/ui/BrandLogo'
import { Button, Input } from '@/components/ui'
import { useAuthStore } from '@/store/authStore'
import { auth } from '@/services/api'
import { useFormErrors } from '@/hooks/useFormErrors'
import { useSubmitGuard } from '@/hooks/useSubmitGuard'
import { ICON } from '@/constants/iconSizes'

export default function Login() {
  const navigate = useNavigate()
  const { login: setAuth } = useAuthStore()

  const [form, setForm] = useState({ phone: '', password: '' })
  const { errors, clearFieldError, applyErrors } = useFormErrors()
  const [showPwd, setShowPwd] = useState(false)
  const { isSubmitting, runSubmit } = useSubmitGuard({
    onError: (err) => toast.error(err.message || '登录失败，请检查手机号和密码'),
  })

  const validate = () => {
    const next = {}
    if (!form.phone) next.phone = '请输入手机号'
    else if (!/^1[3-9]\d{9}$/.test(form.phone)) next.phone = '请输入有效的 11 位手机号'
    if (!form.password) next.password = '请输入密码'
    else if (form.password.length < 8) next.password = '密码至少 8 位'
    return next
  }

  const handleChange = (k, v) => {
    setForm((f) => ({ ...f, [k]: v }))
    if (errors[k]) clearFieldError(k)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!applyErrors(validate())) return
    await runSubmit(async () => {
      const data = await auth.login(form)
      setAuth(data.user || data, data.access, data.refresh)
      navigate('/member')
    })
  }

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
          <BrandLogo variant="consumer" size="md" to="/" className="justify-center mb-4" />
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
            <Input
              label="手机号"
              type="tel"
              placeholder="请输入 11 位手机号"
              value={form.phone}
              onChange={(e) => handleChange('phone', e.target.value)}
              leftIcon={<Phone className={ICON.lg} />}
              error={errors.phone}
              maxLength={11}
              inputClassName="py-3.5 pl-12"
            />

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
                <Input
                  type={showPwd ? 'text' : 'password'}
                  placeholder="请输入密码"
                  value={form.password}
                  onChange={(e) => handleChange('password', e.target.value)}
                  leftIcon={<Lock className={ICON.lg} />}
                  error={errors.password}
                  inputClassName="py-3.5 pl-12 pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-navy-400 hover:text-gold-400 transition-colors"
                >
                  {showPwd ? <EyeOff className={ICON.lg} /> : <Eye className={ICON.lg} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="gold"
              size="lg"
              isLoading={isSubmitting}
              iconLeft={<LogIn className={ICON.lg} />}
              className="w-full py-4 text-lg"
            >
              {isSubmitting ? '登录中…' : '登录账号'}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-navy-600/30 text-center">
            <p className="text-navy-300">
              还没有账号？{' '}
              <Link to="/register" className="text-gold-400 font-semibold hover:text-gold-300 transition-colors inline-flex items-center gap-1">
                立即注册 <ArrowRight className={ICON.md} />
              </Link>
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-10 grid grid-cols-1 gap-3 text-center sm:grid-cols-3 sm:gap-4"
        >
          {[
            { icon: Zap, label: '极速生成' },
            { icon: Sparkles, label: '智能创作' },
            { icon: Shield, label: '安全可靠' },
          ].map((item) => (
            <div key={item.label} className="p-4 rounded-2xl glass-card">
              <item.icon className={`${ICON.lg} text-gold-400 mx-auto mb-2`} />
              <div className="text-xs text-navy-300">{item.label}</div>
            </div>
          ))}
        </motion.div>
      </motion.div>
    </div>
  )
}
