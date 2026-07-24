import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { authApi, logoutLocal, persistLogin } from '@/services/auth'
import { readAuth, type PersistedAuth } from '@/services/tokenStorage'
import { formatApiError } from '@/services/errors'

type AuthContextValue = {
  auth: PersistedAuth | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<PersistedAuth | null>(() => readAuth())

  const login = useCallback(async (username: string, password: string) => {
    try {
      const tokens = await authApi.login({ username, password })
      // 先落 token，后续 /me 才能带 Authorization
      persistLogin(tokens)
      let user = tokens.user
      try {
        const me = await authApi.me()
        user = {
          id: String(me?.id ?? ''),
          nickname: me?.username,
          username: me?.username,
          email: me?.email,
          is_staff: Boolean(me?.is_staff),
        }
      } catch {
        // me 失败不阻塞登录
      }
      const next = persistLogin({ ...tokens, user })
      setAuth(next)
    } catch (err) {
      throw new Error(formatApiError(err))
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout(auth?.refreshToken)
    } catch {
      // local logout still proceeds
    } finally {
      logoutLocal()
      setAuth(null)
    }
  }, [auth?.refreshToken])

  const value = useMemo(
    () => ({
      auth,
      isAuthenticated: Boolean(auth?.accessToken),
      login,
      logout,
    }),
    [auth, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
