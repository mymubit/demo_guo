const AUTH_STORAGE_KEY = 'scriptforge-auth'

export type PersistedAuth = {
  accessToken: string
  refreshToken: string
  user?: {
    id: string
    nickname?: string
    username?: string
    email?: string
    is_staff?: boolean
  }
}

export function readAuth(): PersistedAuth | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    if (!raw.startsWith('{')) {
      return { accessToken: raw, refreshToken: '' }
    }
    const parsed = JSON.parse(raw) as PersistedAuth | { state: PersistedAuth }
    if ('state' in parsed && parsed.state) return parsed.state
    return parsed as PersistedAuth
  } catch {
    return null
  }
}

export function writeAuth(auth: PersistedAuth): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth))
}

export function clearAuth(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}

export function getAccessToken(): string | null {
  return readAuth()?.accessToken ?? null
}

export function getRefreshToken(): string | null {
  return readAuth()?.refreshToken ?? null
}
