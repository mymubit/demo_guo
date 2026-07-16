import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clapperboard } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner } from '@/components/ui/Tabs'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
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
      await login(username.trim(), password)
      navigate('/projects', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-full min-w-pc items-center justify-center overflow-hidden bg-canvas px-10 py-12">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse 80% 60% at 15% 10%, rgba(10,22,40,0.08), transparent 55%), radial-gradient(ellipse 70% 50% at 90% 85%, rgba(244,183,25,0.12), transparent 50%), linear-gradient(165deg, #f7f8fa 0%, #eef1f5 45%, #f4f5f7 100%)',
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%230a1628\' fill-opacity=\'0.04\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
        }}
      />

      <div className="relative grid w-full max-w-5xl gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <div className="max-w-lg">
          <div className="flex items-center gap-3">
            <Clapperboard className="h-10 w-10 text-navy-900" strokeWidth={1.75} />
            <span className="text-4xl font-semibold tracking-tight text-navy-900">ScriptForge</span>
          </div>
          <p className="mt-5 text-lg leading-snug text-ink">短剧创作，从选题到质检一站完成</p>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-ink-muted">
            立项简报、故事蓝图、分集设计与正文质检环，在同一 PC 工作台连贯推进。
          </p>
        </div>

        <form onSubmit={onSubmit} className="sf-panel w-full space-y-5 p-8">
          <div>
            <h1 className="text-xl font-semibold text-ink">登录</h1>
            <p className="mt-1 text-sm text-ink-muted">使用账号进入创作工作台</p>
          </div>
          {error ? <ErrorBanner message={error} /> : null}
          <div>
            <label className="sf-label" htmlFor="username">
              账号
            </label>
            <input
              id="username"
              className="sf-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              placeholder="用户名"
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
