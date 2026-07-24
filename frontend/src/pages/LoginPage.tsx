import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Clapperboard, Eye, EyeOff, LockKeyhole } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard', { replace: true })
  }, [isAuthenticated, navigate])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await login(username.trim(), password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid min-h-dvh bg-[#f4f5f2] lg:grid-cols-[minmax(360px,42%)_1fr]">
      <aside className="hidden flex-col justify-between bg-[#171918] p-10 text-white lg:flex">
        <div>
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center bg-[#d7ff45] text-[#171918]">
              <Clapperboard className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-semibold">ScriptForge</div>
              <div className="text-[10px] tracking-[.12em] text-zinc-500">短剧剧本创作一体机</div>
            </div>
          </div>
          <div className="mt-24 max-w-xs">
            <div className="text-[10px] tracking-[.12em] text-zinc-500">从选题到成稿，一站式短剧创作</div>
            <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight">
              进入你的
              <br />
              <span className="text-[#d7ff45]">创作工作台</span>
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <span className="h-2 w-2 bg-[#d7ff45]" />
          服务就绪
        </div>
      </aside>
      <main className="flex items-center justify-center p-5 sm:p-10">
        <div className="w-full max-w-[420px]">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="grid h-9 w-9 place-items-center bg-[#1b1d1c] text-[#d7ff45]">
              <Clapperboard className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-semibold">ScriptForge</div>
              <div className="text-[10px] tracking-[.12em] text-zinc-500">短剧剧本创作一体机</div>
            </div>
          </div>
          <form
            onSubmit={submit}
            className="border border-black/10 bg-white p-6 shadow-[0_18px_55px_rgba(21,25,22,.08)] sm:p-8"
          >
            <div className="flex h-10 w-10 items-center justify-center bg-[#eef3dc] text-[#6f8c12]">
              <LockKeyhole className="h-4 w-4" />
            </div>
            <h2 className="mt-6 text-2xl font-semibold">登录</h2>
            <p className="mt-2 text-sm text-zinc-500">使用工作空间账号继续。</p>
            {error ? (
              <div className="mt-5 border border-red-200 bg-red-50 p-3 text-xs text-red-800">{error}</div>
            ) : null}
            <label className="mt-7 block text-xs font-medium">
              账号
              <input
                id="username"
                required
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-2 h-11 w-full border border-black/15 px-3 text-sm outline-none focus:border-[#89aa22]"
                placeholder="用户名"
              />
            </label>
            <label className="mt-4 block text-xs font-medium">
              密码
              <span className="relative mt-2 block">
                <input
                  id="password"
                  required
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-11 w-full border border-black/15 px-3 pr-11 text-sm outline-none focus:border-[#89aa22]"
                />
                <button
                  type="button"
                  aria-label={showPassword ? '隐藏密码' : '显示密码'}
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute inset-y-0 right-0 grid w-11 place-items-center text-zinc-500 hover:text-zinc-800"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </span>
            </label>
            <button
              disabled={loading}
              className="mt-6 flex h-11 w-full items-center justify-between bg-[#1b1d1c] px-4 text-sm font-semibold text-white disabled:opacity-50"
            >
              {loading ? '验证中…' : '进入工作台'}
              <ArrowRight className="h-4 w-4 text-[#d7ff45]" />
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}
