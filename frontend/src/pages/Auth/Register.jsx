import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  Phone,
  Lock,
  Eye,
  EyeOff,
  User,
  Loader2,
  UserPlus,
  Check,
  AlertCircle,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { auth } from '@/services/api'
import AuthShell from './AuthShell'

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
    `sf-control pl-12 ${hasError ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/20' : ''}`

  return (
    <AuthShell activeTab="register" title="创建账号" subtitle="注册即送创作币体验">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-2 block text-sm font-medium text-navy-200">手机号</label>
          <div className="relative">
            <Phone className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-navy-400" />
            <input
              type="tel"
              placeholder="请输入 11 位手机号"
              value={form.phone}
              onChange={(e) => handleChange('phone', e.target.value.replace(/\D/g, ''))}
              className={inputClass(errors.phone)}
              maxLength={11}
            />
          </div>
          {errors.phone && <p className="mt-1.5 text-sm text-red-400">{errors.phone}</p>}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-navy-200">
            密码 <span className="font-normal text-navy-400">(至少 8 位)</span>
          </label>
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-navy-400" />
            <input
              type={showPwd ? 'text' : 'password'}
              placeholder="请输入密码"
              value={form.password}
              onChange={(e) => handleChange('password', e.target.value)}
              className={`${inputClass(errors.password)} pr-12`}
            />
            <button
              type="button"
              onClick={() => setShowPwd(!showPwd)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-navy-400 transition-colors hover:text-gold-400"
            >
              {showPwd ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
          {form.password && (
            <div className="mt-2 flex items-center gap-3">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
                <div
                  className={`h-full transition-all duration-300 ${passwordStrength.color}`}
                  style={{ width: `${(passwordStrength.level / 4) * 100}%` }}
                />
              </div>
              <span className="w-12 text-right text-xs text-navy-300">{passwordStrength.label}</span>
            </div>
          )}
          {errors.password && <p className="mt-1.5 text-sm text-red-400">{errors.password}</p>}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-navy-200">确认密码</label>
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-navy-400" />
            <input
              type={showConfirm ? 'text' : 'password'}
              placeholder="请再次输入密码"
              value={form.confirmPassword}
              onChange={(e) => handleChange('confirmPassword', e.target.value)}
              className={`${inputClass(errors.confirmPassword)} pr-12`}
            />
            <button
              type="button"
              onClick={() => setShowConfirm(!showConfirm)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-navy-400 transition-colors hover:text-gold-400"
            >
              {showConfirm ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
          {form.confirmPassword && form.confirmPassword === form.password && (
            <div className="mt-1.5 flex items-center gap-1.5 text-sm text-green-400">
              <Check className="h-4 w-4" /> 两次密码输入一致
            </div>
          )}
          {errors.confirmPassword && <p className="mt-1.5 text-sm text-red-400">{errors.confirmPassword}</p>}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-navy-200">
            昵称 <span className="font-normal text-navy-400">(可选)</span>
          </label>
          <div className="relative">
            <User className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-navy-400" />
            <input
              type="text"
              placeholder="给自己起一个好听的名字"
              value={form.nickname}
              onChange={(e) => handleChange('nickname', e.target.value)}
              className={inputClass(errors.nickname)}
              maxLength={20}
            />
          </div>
          {errors.nickname && <p className="mt-1.5 text-sm text-red-400">{errors.nickname}</p>}
        </div>

        <div className="flex items-start gap-2 pt-1 text-xs text-navy-300">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-gold-400" />
          <span>
            注册即表示您同意我们的
            <Link to="#" className="mx-0.5 text-gold-400 hover:text-gold-300">
              服务条款
            </Link>
            和
            <Link to="#" className="mx-0.5 text-gold-400 hover:text-gold-300">
              隐私政策
            </Link>
          </span>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-xl py-4 text-lg font-bold text-navy-950 transition-all disabled:cursor-not-allowed disabled:opacity-60"
          style={{
            background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
            boxShadow: '0 10px 30px -10px rgba(244, 183, 25, 0.5)',
          }}
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              创建账号中...
            </>
          ) : (
            <>
              <UserPlus className="h-5 w-5" />
              立即注册
            </>
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-navy-300">
        已有账号？{' '}
        <Link to="/login" className="font-semibold text-gold-400 transition-colors hover:text-gold-300">
          立即登录
        </Link>
      </p>
    </AuthShell>
  )
}
