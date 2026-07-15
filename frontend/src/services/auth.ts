import { request } from './http'
import { clearAuth, writeAuth, type PersistedAuth } from './tokenStorage'
import type { LoginResponse } from '@/types/domain'

export const authApi = {
  login(payload: { phone?: string; username?: string; password: string }) {
    return request<LoginResponse>('POST', '/api/auth/login/', {
      data: payload,
      skipAuthRefresh: true,
    })
  },
  refresh(refreshToken: string) {
    return request<{ access: string }>('POST', '/api/auth/refresh/', {
      data: { refresh: refreshToken },
      rawResponse: true,
      skipAuthRefresh: true,
    })
  },
  logout(refreshToken?: string) {
    return request<null>('POST', '/api/auth/logout/', {
      data: refreshToken ? { refresh: refreshToken } : {},
      skipAuthRefresh: true,
    })
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
