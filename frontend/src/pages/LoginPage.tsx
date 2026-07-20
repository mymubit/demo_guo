import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clapperboard, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner } from '@/components/ui/Tabs'

const BRAND_STEPS = ['选题定调', '故事蓝图', '分集写作', '质检闭环'] as const

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
    <div className="flex min-h-full min-w-pc">
      {/* 影棚品牌平面：占满左半屏 */}
      <aside className="relative hidden w-[46%] shrink-0 flex-col justify-between overflow-hidden bg-shell px-12 py-14 text-shell-ink lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            background:
              'radial-gradient(ellipse 70% 50% at 20% 15%, rgba(244,183,25,0.22), transparent 55%), radial-gradient(ellipse 60% 45% at 90% 90%, rgba(255,255,255,0.06), transparent 50%)',
          }}
        />
        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-shell-accent/15 ring-1 ring-shell-accent/40">
              <Clapperboard className="h-6 w-6 text-shell-accent" strokeWidth={1.75} />
            </div>
            <div>
              <div className="text-2xl font-semibold tracking-tight text-white">ScriptForge</div>
              <div className="text-xs tracking-wide text-shell-muted">短剧工业化创作台</div>
            </div>
          </div>
          <h1 className="mt-14 max-w-md text-4xl font-semibold leading-tight tracking-tight text-white">
            从选题到质检，
            <span className="text-shell-accent">一条流水线</span>
          </h1>
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-shell-muted">
            立项简报、故事蓝图、分集设计与正文质检环，在同一 PC 工作台连贯推进。
          </p>
        </div>
        <ol className="relative space-y-3">
          {BRAND_STEPS.map((step, index) => (
            <li key={step} className="flex items-center gap-3 text-sm text-shell-ink">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-white/5 text-xs font-semibold text-shell-accent ring-1 ring-white/10">
                {index + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </aside>

      {/* 冷雾登录区 */}
      <main className="relative flex flex-1 items-center justify-center bg-canvas px-10 py-12">
        <div
          className="pointer-events-none absolute inset-0 opacity-60"
          style={{
            background:
              'radial-gradient(ellipse 50% 40% at 80% 20%, rgba(15,39,68,0.06), transparent 55%)',
          }}
        />
        <div className="relative w-full max-w-md">
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <Clapperboard className="h-7 w-7 text-action" />
            <span className="text-xl font-semibold text-ink">ScriptForge</span>
          </div>
          <form onSubmit={onSubmit} className="sf-panel space-y-5 p-8 shadow-panel">
            <div>
              <div className="mb-1 flex items-center gap-2 text-action">
                <Sparkles className="h-4 w-4" />
                <span className="text-xs font-medium tracking-wide">工作台入口</span>
              </div>
              <h2 className="text-2xl font-semibold tracking-tight text-ink">登录</h2>
              <p className="mt-1.5 text-sm text-ink-muted">使用账号进入创作与运维空间</p>
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
            <Button type="submit" variant="action" className="w-full" size="lg" loading={loading}>
              进入工作台
            </Button>
          </form>
        </div>
      </main>
    </div>
  )
}
