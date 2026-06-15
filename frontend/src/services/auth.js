import { request } from './http'

export const auth = {
  login({ phone, password }) {
    return request('POST', '/api/auth/login/', { data: { phone, password } })
  },
  register({ phone, password, password_confirm, nickname }) {
    return request('POST', '/api/auth/register/', {
      data: { phone, password, password_confirm, nickname },
    })
  },
  logout(refreshToken) {
    return request('POST', '/api/auth/logout/', {
      data: { refresh: refreshToken },
      skipAuthRefresh: true,
    })
  },
  refresh(refreshToken) {
    return request('POST', '/api/auth/refresh/', {
      data: { refresh: refreshToken },
      rawResponse: true,
      skipAuthRefresh: true,
    })
  },
  verify(token) {
    return request('POST', '/api/auth/verify/', {
      data: { token },
      rawResponse: true,
      skipAuthRefresh: true,
    })
  },
}
