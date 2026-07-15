import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'
import { ApiError, API_ERROR_CODES, AUTH_ERROR_CODES } from './errors'
import { clearAuth, getAccessToken, getRefreshToken, readAuth, writeAuth } from './tokenStorage'

export const API_BASE_URL =
  typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL != null
    ? String(import.meta.env.VITE_API_BASE_URL)
    : ''

const AUTH_REFRESH_PATH = '/api/auth/refresh/'

type RequestOptions = {
  params?: Record<string, unknown>
  data?: unknown
  headers?: Record<string, string>
  rawResponse?: boolean
  skipAuthRefresh?: boolean
  signal?: AbortSignal
}

type Envelope = {
  code?: number
  message?: string
  data?: unknown
}

let axiosInstance: AxiosInstance | null = null
let refreshPromise: Promise<string | null> | null = null

function unwrapEnvelope(raw: unknown, rawResponse?: boolean): unknown {
  if (rawResponse) return raw
  if (!raw || typeof raw !== 'object') return raw
  const body = raw as Envelope
  if (typeof body.code !== 'number') return raw
  if (body.code === API_ERROR_CODES.SUCCESS) return body.data ?? null
  throw new ApiError({
    message: body.message,
    code: body.code,
    data: body.data,
  })
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null
  if (refreshPromise) return refreshPromise

  refreshPromise = axios
    .post(
      `${API_BASE_URL}${AUTH_REFRESH_PATH}`,
      { refresh: refreshToken },
      { headers: { 'Content-Type': 'application/json' } },
    )
    .then((resp) => {
      const body = resp.data as { access?: string; data?: { access?: string } }
      const access = body.access ?? body.data?.access ?? null
      if (!access) return null
      const prev = readAuth()
      writeAuth({
        accessToken: access,
        refreshToken: prev?.refreshToken ?? refreshToken,
        user: prev?.user,
      })
      return access
    })
    .catch(() => null)
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

export function clearAuthAndRedirect(): void {
  clearAuth()
  if (typeof window === 'undefined') return
  const path = window.location.pathname
  if (path !== '/login') {
    window.location.href = '/login'
  }
}

function getClient(): AxiosInstance {
  if (axiosInstance) return axiosInstance

  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120_000,
    headers: { 'Content-Type': 'application/json' },
  })

  instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  instance.interceptors.response.use(
    (response) => {
      const rawResponse = Boolean((response.config as AxiosRequestConfig & { rawResponse?: boolean }).rawResponse)
      response.data = unwrapEnvelope(response.data, rawResponse)
      return response
    },
    async (error) => {
      const config = error.config as (AxiosRequestConfig & {
        skipAuthRefresh?: boolean
        _retryAfterRefresh?: boolean
        rawResponse?: boolean
      }) | undefined
      const status = error.response?.status as number | undefined
      const body = error.response?.data as Envelope | undefined

      if (
        status === 401 &&
        config &&
        !config.skipAuthRefresh &&
        !config._retryAfterRefresh &&
        body?.code !== API_ERROR_CODES.SIGNATURE_INVALID
      ) {
        const access = await refreshAccessToken()
        if (access) {
          config._retryAfterRefresh = true
          config.headers = {
            ...(config.headers ?? {}),
            Authorization: `Bearer ${access}`,
          }
          return instance.request(config)
        }
        clearAuthAndRedirect()
      }

      if (body && typeof body === 'object' && typeof body.code === 'number') {
        throw new ApiError({
          message: body.message,
          code: body.code,
          data: body.data,
          httpStatus: status,
        })
      }

      if (AUTH_ERROR_CODES.has(body?.code ?? -1) || status === 401) {
        throw new ApiError({
          message: body?.message,
          code: body?.code ?? API_ERROR_CODES.UNAUTHORIZED,
          httpStatus: status,
        })
      }

      throw new ApiError({
        message: body?.message || error.message,
        code: body?.code,
        httpStatus: status,
        fallbackMessage: '网络异常，请稍后重试',
      })
    },
  )

  axiosInstance = instance
  return instance
}

export async function request<T = unknown>(
  method: string,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const client = getClient()
  const response = await client.request({
    method,
    url: path,
    params: options.params,
    data: options.data,
    headers: options.headers,
    signal: options.signal,
    rawResponse: options.rawResponse,
    skipAuthRefresh: options.skipAuthRefresh,
  } as AxiosRequestConfig)
  return response.data as T
}

export const http = {
  get: <T>(path: string, options?: RequestOptions) => request<T>('GET', path, options),
  post: <T>(path: string, data?: unknown, options?: RequestOptions) =>
    request<T>('POST', path, { ...options, data }),
  put: <T>(path: string, data?: unknown, options?: RequestOptions) =>
    request<T>('PUT', path, { ...options, data }),
  patch: <T>(path: string, data?: unknown, options?: RequestOptions) =>
    request<T>('PATCH', path, { ...options, data }),
  delete: <T>(path: string, options?: RequestOptions) => request<T>('DELETE', path, options),
}

export default request
