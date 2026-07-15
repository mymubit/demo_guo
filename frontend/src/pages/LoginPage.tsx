import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clapperboard } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner } from '@/components/ui/Tabs'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated) navigate('/projects', { replace: true })
  }, [isAuthenticated, navigate])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(phone.trim(), password)
      navigate('/projects', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-full min-w-pc items-stretch bg-navy-900">
      <div className="relative flex w-[42%] flex-col justify-between overflow-hidden px-12 py-14 text-white">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            background:
              'radial-gradient(ellipse at 20% 20%, rgba(99,102,241,0.35), transparent 55%), radial-gradient(ellipse at 80% 80%, rgba(244,183,25,0.18), transparent 50%)',
          }}
        />
        <div className="relative">
          <div className="flex items-center gap-3">
            <Clapperboard className="h-8 w-8 text-gold-400" />
            <span className="text-2xl font-semibold tracking-wide">ScriptForge</span>
          </div>
          <p className="mt-8 max-w-sm text-sm leading-relaxed text-slate-300">
            短剧创作工作台。选题定调、剧本蓝图、分集设计、正文与质检环，在同一 PC 工作台完成。
          </p>
        </div>
        <p className="relative text-xs text-slate-500">PC 端专业工作台 · JWT 接入</p>
      </div>

      <div className="flex flex-1 items-center justify-center bg-canvas px-10">
        <form onSubmit={onSubmit} className="w-full max-w-md space-y-5">
          <div>
            <h1 className="text-2xl font-semibold text-ink">登录</h1>
            <p className="mt-1 text-sm text-ink-muted">使用账号进入创作工作台</p>
          </div>
          {error ? <ErrorBanner message={error} /> : null}
          <div>
            <label className="sf-label" htmlFor="phone">
              手机号 / 账号
            </label>
            <input
              id="phone"
              className="sf-control"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="sf-label" htmlFor="password">
              密码
            </label>
            <input
              id="password"
              type="password"
              className="sf-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <Button type="submit" className="w-full" size="lg" loading={loading}>
            进入工作台
          </Button>
        </form>
      </div>
    </div>
  )
}
