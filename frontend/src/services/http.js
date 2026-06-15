/**
 * http.js —— axios 单例 + 请求基础层
 *
 * 职责：
 *   1. 维护 axios 懒加载单例（避免重复初始化）
 *   2. 请求拦截：自动附加 Authorization Header
 *   3. 响应拦截：解包 {code, data, message}，处理 401/429
 *   4. 提供统一 request() 入口（axios + fetch 双轨）
 */

import { formatUserError } from '@/utils/userError'
import { useRequestUiStore } from '@/store/requestUiStore'
import { useAuthStore } from '@/store/authStore'
import { installAxiosMonitor } from '@/utils/monitor'
import {
  API_ERROR_CODES,
  API_SUCCESS_CODE,
  AUTH_ERROR_CODES,
  PERMISSION_ERROR_CODES,
  RATE_LIMIT_ERROR_CODES,
} from './constants/errorCodes'

export const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
  'http://localhost:8000'

const API_SIGN_SECRET =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_SIGN_SECRET) ||
  ''

const AUTH_STORAGE_KEY = 'scriptforge-auth'
const AUTH_REFRESH_PATH = '/api/auth/refresh/'

let _axiosInstance = null
let _refreshPromise = null

function bytesToHex(buffer) {
  return Array.from(new Uint8Array(buffer))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
}

function createNonce() {
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    const bytes = new Uint8Array(16)
    crypto.getRandomValues(bytes)
    return Array.from(bytes).map((byte) => byte.toString(16).padStart(2, '0')).join('')
  }
  return `${Date.now()}${Math.random().toString(16).slice(2)}`
}

function normalizeBodyForSigning(data) {
  if (data === undefined || data === null) return ''
  if (typeof data === 'string') return data
  if (typeof Blob !== 'undefined' && data instanceof Blob) return ''
  if (typeof FormData !== 'undefined' && data instanceof FormData) return ''
  return JSON.stringify(data)
}

function normalizeSignPath(url) {
  const raw = String(url || '')
  try {
    const parsed = raw.startsWith('http') ? new URL(raw) : new URL(raw, API_BASE_URL)
    return parsed.pathname
  } catch {
    return raw.split('?')[0] || '/'
  }
}

async function sha256Hex(text) {
  const data = new TextEncoder().encode(text || '')
  const digest = await crypto.subtle.digest('SHA-256', data)
  return bytesToHex(digest)
}

async function hmacSha256Hex(secret, message) {
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  )
  const signature = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(message))
  return bytesToHex(signature)
}

async function buildSignatureHeaders(method, path, data) {
  if (!API_SIGN_SECRET || typeof crypto === 'undefined' || !crypto.subtle) return {}
  const timestamp = Math.floor(Date.now() / 1000).toString()
  const nonce = createNonce()
  const bodyHash = await sha256Hex(normalizeBodyForSigning(data))
  const signPath = normalizeSignPath(path)
  const signString = `${String(method || '').toUpperCase()}${signPath}${timestamp}${nonce}${bodyHash}`
  const signature = await hmacSha256Hex(API_SIGN_SECRET, signString)
  return {
    'X-Timestamp': timestamp,
    'X-Nonce': nonce,
    'X-Body-Hash': bodyHash,
    'X-Signature': signature,
  }
}

function createApiError({
  message,
  code,
  data,
  httpStatus,
  fallbackMessage = '请求失败',
}) {
  const normalizedCode = code ?? httpStatus ?? API_ERROR_CODES.SERVER_ERROR
  const err = new Error(formatUserError(message, fallbackMessage))
  err.code = normalizedCode
  err.data = data
  err.httpStatus = httpStatus
  err.isAuthError = AUTH_ERROR_CODES.has(normalizedCode) || httpStatus === 401
  err.isPermissionError = PERMISSION_ERROR_CODES.has(normalizedCode) || httpStatus === 403
  err.isRateLimited = RATE_LIMIT_ERROR_CODES.has(normalizedCode) || httpStatus === 429
  return err
}

function readPersistedAuthState() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    if (!raw.startsWith('{')) return { token: raw }
    const obj = JSON.parse(raw)
    return obj.state && typeof obj.state === 'object' ? obj.state : obj
  } catch {
    return null
  }
}

/** 从 localStorage 读取 access token（兼容 zustand persist 格式） */
export function getAccessToken() {
  const payload = readPersistedAuthState()
  return payload?.token || payload?.access || payload?.accessToken || null
}

export function getRefreshToken() {
  const payload = readPersistedAuthState()
  return payload?.refreshToken || payload?.refresh || null
}

function persistAccessToken(accessToken) {
  if (!accessToken) return
  try {
    useAuthStore.getState().setToken(accessToken)
  } catch {
    // Zustand 未初始化时继续写 localStorage 兜底
  }
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw || !raw.startsWith('{')) {
      localStorage.setItem(AUTH_STORAGE_KEY, accessToken)
      return
    }
    const obj = JSON.parse(raw)
    const state = obj.state && typeof obj.state === 'object' ? obj.state : obj
    const next = {
      ...obj,
      state: {
        ...state,
        token: accessToken,
        access: accessToken,
        accessToken,
        isAuthenticated: true,
      },
    }
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(next))
  } catch {
    // ignore
  }
}

/** 清除登录态并跳转到对应登录页 */
export function clearAuthAndRedirect() {
  try {
    useAuthStore.getState().logout()
  } catch {
    // ignore
  }
  try {
    localStorage.removeItem(AUTH_STORAGE_KEY)
  } catch {
    // ignore
  }
  if (typeof window !== 'undefined') {
    const path = window.location.pathname
    const loginPath = path.startsWith('/admin') ? '/admin/login' : '/login'
    if (path !== loginPath) {
      window.location.href = loginPath
    }
  }
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null
  if (_refreshPromise) return _refreshPromise

  _refreshPromise = fetch(API_BASE_URL + AUTH_REFRESH_PATH, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken }),
  })
    .then(async (resp) => {
      if (!resp.ok) return null
      const body = await resp.json()
      const accessToken = body?.access || null
      if (accessToken) persistAccessToken(accessToken)
      return accessToken
    })
    .catch(() => null)
    .finally(() => {
      _refreshPromise = null
    })

  return _refreshPromise
}

async function retryWithRefresh(config, retry) {
  if (!config || config.skipAuthRefresh || config._retryAfterRefresh) return null
  if (config.url && String(config.url).includes(AUTH_REFRESH_PATH)) return null
  const accessToken = await refreshAccessToken()
  if (!accessToken) return null
  const nextConfig = {
    ...config,
    _retryAfterRefresh: true,
    headers: {
      ...(config.headers || {}),
      Authorization: `Bearer ${accessToken}`,
    },
  }
  return retry(nextConfig)
}

/** 解析后端 {code, message, data} 响应体，特殊接口可通过 rawResponse 跳过 */
async function parseResponse(raw, config) {
  if (config?.rawResponse) return raw
  if (!raw || typeof raw !== 'object') return raw
  if (typeof raw.code === 'number') {
    if (raw.code === API_SUCCESS_CODE) {
      if (raw.pagination != null) {
        return { data: raw.data, pagination: raw.pagination }
      }
      return raw.data
    }

    if (AUTH_ERROR_CODES.has(raw.code)) {
      const retryResult = await retryWithRefresh(config, (nextConfig) =>
        _axiosInstance.request(nextConfig)
      )
      if (retryResult) return retryResult
      clearAuthAndRedirect()
    }
    throw createApiError({ message: raw.message, code: raw.code, data: raw.data })
  }
  return raw
}

/** 获取 axios 单例（懒加载，不可用时返回 null） */
export async function getAxios() {
  if (_axiosInstance) return _axiosInstance
  try {
    const mod = await import('axios')
    const axios = mod.default || mod
    const instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: { 'Content-Type': 'application/json' },
    })

    installAxiosMonitor(instance)

    instance.interceptors.request.use(async (config) => {
      const token = getAccessToken()
      config.headers = config.headers || {}
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      const signatureHeaders = await buildSignatureHeaders(
        config.method || 'GET',
        config.url || '',
        config.data
      )
      Object.assign(config.headers, signatureHeaders)
      return config
    })

    instance.interceptors.response.use(
      (response) => parseResponse(response.data, response.config),
      async (error) => {
        if (error?.response) {
          const body = error.response.data
          if (
            error.response.status === 401 &&
            body?.code !== API_ERROR_CODES.SIGNATURE_INVALID
          ) {
            const retryResult = await retryWithRefresh(error.config, (nextConfig) =>
              instance.request(nextConfig)
            )
            if (retryResult) return retryResult
            clearAuthAndRedirect()
          }
          if (error.response.status === 429) {
            const body = error.response.data
            const resetAfter =
              body?.detail?.reset_after ?? error.response.headers?.['x-ratelimit-reset']
            const baseMsg =
              body && typeof body.message === 'string'
                ? body.message
                : '请求已被限流，请稍后再试'
            return Promise.reject(
              createApiError({
                message:
                  resetAfter != null && !baseMsg.includes('秒')
                    ? `${baseMsg.replace(/。?$/, '')}，预计 ${resetAfter} 秒后可用`
                    : baseMsg,
                code: body?.code ?? API_ERROR_CODES.RATE_LIMITED,
                data: body?.detail,
                httpStatus: 429,
                fallbackMessage: '请求已被限流，请稍后再试',
              })
            )
          }
          if (body && typeof body === 'object' && typeof body.code === 'number') {
            return Promise.reject(
              createApiError({
                message: body.message,
                code: body.code,
                data: body.data,
                httpStatus: error.response.status,
              })
            )
          }
        }
        return Promise.reject(
          createApiError({
            message: error.message,
            httpStatus: error?.response?.status,
            fallbackMessage: '网络异常，请稍后重试',
          })
        )
      }
    )

    _axiosInstance = instance
    return instance
  } catch {
    _axiosInstance = null
    return null
  }
}

/**
 * 通用请求入口：优先 axios，降级 fetch
 */
export async function request(
  method,
  path,
  {
    params,
    data,
    responseType,
    headers,
    globalLoading = false,
    rawResponse = false,
    skipAuthRefresh = false,
  } = {}
) {
  const requestUi = useRequestUiStore.getState()
  if (globalLoading) requestUi.start()

  try {
    const axios = await getAxios()
    if (axios) {
      return await axios.request({
        method,
        url: path,
        params,
        data,
        responseType,
        headers,
        rawResponse,
        skipAuthRefresh,
      })
    }

    // fetch fallback
    const token = getAccessToken()
    const url = new URL(API_BASE_URL + path)
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) url.searchParams.append(k, v)
      })
    }
    const init = {
      method: method.toUpperCase(),
      headers: { 'Content-Type': 'application/json', ...(headers || {}) },
    }
    if (token) init.headers.Authorization = `Bearer ${token}`
    if (data !== undefined && data !== null) init.body = JSON.stringify(data)
    Object.assign(init.headers, await buildSignatureHeaders(method, url.pathname, init.body || ''))

    let resp = await fetch(url.toString(), init)
    let unauthorizedBody = null
    if (resp.status === 401) {
      try {
        unauthorizedBody = await resp.clone().json()
      } catch {
        unauthorizedBody = null
      }
    }
    if (
      resp.status === 401 &&
      unauthorizedBody?.code !== API_ERROR_CODES.SIGNATURE_INVALID &&
      !skipAuthRefresh
    ) {
      const accessToken = await refreshAccessToken()
      if (accessToken) {
        init.headers.Authorization = `Bearer ${accessToken}`
        Object.assign(init.headers, await buildSignatureHeaders(method, url.pathname, init.body || ''))
        resp = await fetch(url.toString(), init)
      } else {
        clearAuthAndRedirect()
        throw createApiError({
          message: '未登录或登录已过期',
          code: API_ERROR_CODES.UNAUTHORIZED,
          httpStatus: 401,
        })
      }
    }
    if (responseType === 'blob') {
      if (!resp.ok) {
        throw createApiError({
          message: `HTTP ${resp.status}`,
          httpStatus: resp.status,
          fallbackMessage: '下载失败，请稍后重试',
        })
      }
      return await resp.blob()
    }
    let body
    try {
      body = await resp.json()
    } catch {
      if (!resp.ok) {
        throw createApiError({
          message: `HTTP ${resp.status}`,
          httpStatus: resp.status,
          fallbackMessage: '网络异常，请稍后重试',
        })
      }
      return null
    }
    if (rawResponse) return body
    if (body && typeof body.code === 'number' && AUTH_ERROR_CODES.has(body.code) && !skipAuthRefresh) {
      const accessToken = await refreshAccessToken()
      if (accessToken) {
        init.headers.Authorization = `Bearer ${accessToken}`
        Object.assign(init.headers, await buildSignatureHeaders(method, url.pathname, init.body || ''))
        const retryResp = await fetch(url.toString(), init)
        const retryBody = await retryResp.json()
        return parseResponse(retryBody)
      }
      clearAuthAndRedirect()
    }
    return parseResponse(body)
  } finally {
    if (globalLoading) requestUi.finish()
  }
}

export default request
