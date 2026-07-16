import { request } from './http'
import { clearAuth, writeAuth, type PersistedAuth } from './tokenStorage'
import type { LoginResponse } from '@/types/domain'

export const authApi = {
  login(payload: { username: string; password: string }) {
    const username = payload.username.trim()
    return request<LoginResponse>('POST', '/api/v1/auth/token/', {
      data: { username, password: payload.password },
      skipAuthRefresh: true,
    })
  },
  refresh(refreshToken: string) {
    return request<{ access: string }>('POST', '/api/v1/auth/token/refresh/', {
      data: { refresh: refreshToken },
      skipAuthRefresh: true,
    })
  },
  me() {
    return request<{ id: number | string; username?: string; email?: string; is_staff?: boolean }>(
      'GET',
      '/api/v1/auth/me/',
    )
  },
  logout(_refreshToken?: string) {
    // 后端无专用 logout；由调用方本地清 token
    return Promise.resolve(null)
  },
}

export function persistLogin(result: LoginResponse): PersistedAuth {
  const auth: PersistedAuth = {
    accessToken: result.access,
    refreshToken: result.refresh,
    user: result.user,
  }
  writeAuth(auth)
  return auth
}

export function logoutLocal(): void {
  clearAuth()
}
