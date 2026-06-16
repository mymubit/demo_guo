import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Phone, Lock, Eye, EyeOff, LogIn } from 'lucide-react'
import { Button, Input } from '@/components/ui'
import { useAuthStore } from '@/store/authStore'
import { auth } from '@/services/api'
import { useFormErrors } from '@/hooks/useFormErrors'
import { useSubmitGuard } from '@/hooks/useSubmitGuard'
import { ICON } from '@/constants/iconSizes'
import AuthShell from './AuthShell'

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
    <AuthShell activeTab="login" title="欢迎回来" subtitle="登录以继续你的创作">
      <form onSubmit={handleSubmit} className="space-y-4">
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
          <div className="mb-2 flex items-center justify-between">
            <label className="block text-sm font-medium text-navy-200">密码</label>
            <button
              type="button"
              onClick={() => toast.info('请联系客服或使用手机号重置密码')}
              className="text-sm text-gold-400 transition-colors hover:text-gold-300"
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
              className="absolute right-4 top-1/2 -translate-y-1/2 text-navy-400 transition-colors hover:text-gold-400"
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

      <p className="mt-6 text-center text-sm text-navy-300">
        还没有账号？{' '}
        <Link to="/register" className="font-semibold text-gold-400 transition-colors hover:text-gold-300">
          立即注册
        </Link>
      </p>
    </AuthShell>
  )
}
