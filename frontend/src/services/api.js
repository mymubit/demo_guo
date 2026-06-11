/**
 * api.js —— ScriptForge 前端统一 API 服务层
 *
 * 设计目标：
 *   1. 统一拦截器：自动附带 Authorization 头、统一解析后端响应结构
 *   2. 统一错误处理：code !== 0 视为失败，自动 reject，并对 401 做登出跳登录
 *   3. 模块拆分：auth / users / membership / orders / creation / works / skill
 *   4. 可配置 baseURL：通过 VITE_API_BASE_URL 环境变量，默认 http://localhost:8000
 *   5. 兼容 axios / fetch：优先 axios（若已安装），fallback 到原生 fetch
 *
 * 后端响应约定：{ code: number, message: string, data: any }
 *   - code === 0 ：成功，resolve(data)
 *   - code !== 0 ：失败，reject(message)
 */

const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
  'http://localhost:8000'

const AUTH_STORAGE_KEY = 'scriptforge-auth'

/**
 * 从 localStorage 读取 access token
 * 存储结构可能是字符串（"token"）或 JSON 对象（{access, refresh, user...}）
 */
function getAccessToken() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    if (raw.startsWith('{')) {
      const obj = JSON.parse(raw)
      return obj.access || obj.token || obj.accessToken || null
    }
    return raw
  } catch (e) {
    return null
  }
}

/**
 * 清除登录态并跳转到登录页
 */
function clearAuthAndRedirect() {
  try {
    localStorage.removeItem(AUTH_STORAGE_KEY)
  } catch (e) {
    // ignore
  }
  if (typeof window !== 'undefined') {
    // 避免在 /login 死循环
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }
}

/**
 * 解析后端响应体
 */
function parseResponse(raw) {
  if (!raw || typeof raw !== 'object') {
    return raw
  }
  // 符合 {code, message, data} 结构
  if (typeof raw.code === 'number') {
    if (raw.code === 0) {
      return raw.data
    }
    // 业务级 401
    if (raw.code === 401) {
      clearAuthAndRedirect()
    }
    const err = new Error(raw.message || '请求失败')
    err.code = raw.code
    err.data = raw.data
    throw err
  }
  return raw
}

/**
 * HTTP 层：检测 axios 是否可用，否则使用 fetch
 */
function hasAxios() {
  try {
    // 优先使用动态 require（Vite 场景走 import.meta）
    // 这里通过全局变量与已安装依赖判断
    // 真实调用处使用 try-import
    return true
  } catch (e) {
    return false
  }
}

let _axiosInstance = null

/**
 * axios 实例（懒加载），若 axios 未安装则返回 null
 */
async function getAxios() {
  if (_axiosInstance) return _axiosInstance
  try {
    const mod = await import('axios')
    const axios = mod.default || mod
    const instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
    // 请求拦截器：附加 Authorization
    instance.interceptors.request.use((config) => {
      const token = getAccessToken()
      if (token) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
    // 响应拦截器：解包 data / 处理 401
    instance.interceptors.response.use(
      (response) => parseResponse(response.data),
      (error) => {
        if (error && error.response) {
          if (error.response.status === 401) {
            clearAuthAndRedirect()
          }
          // 尝试解析后端返回的结构化错误
          const body = error.response.data
          if (body && typeof body === 'object' && typeof body.code === 'number') {
            const err = new Error(body.message || '请求失败')
            err.code = body.code
            err.data = body.data
            return Promise.reject(err)
          }
        }
        return Promise.reject(error)
      }
    )
    _axiosInstance = instance
    return instance
  } catch (e) {
    // axios 未安装，使用 fetch fallback
    _axiosInstance = null
    return null
  }
}

/**
 * 通用请求入口：先尝试 axios，失败则使用 fetch
 */
async function request(method, path, { params, data, responseType, headers } = {}) {
  const axios = await getAxios()
  if (axios) {
    return axios.request({
      method,
      url: path,
      params,
      data,
      responseType,
      headers,
    })
  }
  // ------- fetch fallback -------
  const token = getAccessToken()
  const url = new URL(API_BASE_URL + path)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.append(k, v)
    })
  }
  const init = {
    method: method.toUpperCase(),
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {}),
    },
  }
  if (token) init.headers.Authorization = `Bearer ${token}`
  if (data !== undefined && data !== null) init.body = JSON.stringify(data)

  const resp = await fetch(url.toString(), init)
  if (resp.status === 401) {
    clearAuthAndRedirect()
    throw new Error('未登录或登录已过期')
  }
  if (responseType === 'blob') {
    if (!resp.ok) throw new Error('下载失败: ' + resp.status)
    return await resp.blob()
  }
  let body
  try {
    body = await resp.json()
  } catch (e) {
    if (!resp.ok) throw new Error('网络错误: ' + resp.status)
    return null
  }
  return parseResponse(body)
}

// ============================================================
//                          模块：auth
// ============================================================
/**
 * 登录 / 注册 / 登出
 * 接口路径以 /api/auth 前缀
 */
const auth = {
  login({ phone, password }) {
    return request('POST', '/api/auth/login/', { data: { phone, password } })
  },
  register({ phone, password, password_confirm, nickname }) {
    return request('POST', '/api/auth/register/', {
      data: { phone, password, password_confirm, nickname },
    })
  },
  logout(refreshToken) {
    return request('POST', '/api/auth/logout/', { data: { refresh: refreshToken } })
  },
}

// ============================================================
//                          模块：users
// ============================================================
const users = {
  me() {
    return request('GET', '/api/users/me/')
  },
  updateMe(patchData) {
    return request('PUT', '/api/users/me/update/', { data: patchData })
  },
}

// ============================================================
//                        模块：membership
// ============================================================
const membership = {
  /** 获取套餐列表（公共） */
  plans() {
    return request('GET', '/api/membership/plans/')
  },
  /** 当前用户的会员信息 */
  myMembership() {
    return request('GET', '/api/membership/me/')
  },
  /** 会员概览（可能返回额度、到期等汇总信息） */
  summary() {
    return request('GET', '/api/membership/summary/')
  },
  /** 卡密兑换历史 */
  history() {
    return request('GET', '/api/membership/history/')
  },
  /** 卡密兑换 */
  redeem(code) {
    return request('POST', '/api/membership/redeem/', { data: { code } })
  },
}

// ============================================================
//                          模块：orders
// ============================================================
const orders = {
  /** 订单列表，可选按状态过滤 status: 'paid' | 'pending' | 'cancelled' */
  list(status) {
    return request('GET', '/api/orders/', { params: status ? { status } : undefined })
  },
  /** 订单详情 */
  detail(orderId) {
    return request('GET', `/api/orders/${orderId}/`)
  },
  /** 创建订单（下单） */
  createOrder({ plan_id, payment_method }) {
    return request('POST', '/api/orders/create/', {
      data: { plan_id, payment_method },
    })
  },
  /** 演示环境：模拟支付 */
  mockPay(orderNo) {
    return request('POST', '/api/orders/mock_pay/', { data: { order_no: orderNo } })
  },
  /** 取消订单 */
  cancel(orderNo) {
    return request('POST', `/api/orders/${orderNo}/cancel/`)
  },
  /** 最近一笔订单 */
  latest() {
    return request('GET', '/api/orders/latest/')
  },
}

// ============================================================
//                         模块：creation
// ============================================================
const creation = {
  /** 提交创作任务 */
  submit({ theme, core_idea, episode_count, format_variant, audience, reference_work }) {
    return request('POST', '/api/creation/submit/', {
      data: { theme, core_idea, episode_count, format_variant, audience, reference_work },
    })
  },
  /** 查询创作进度 */
  progress(projectId) {
    return request('GET', `/api/creation/progress/${projectId}/`)
  },
  /** 下载创作产物，format: 'markdown' | 'docx' | 'pdf' ... */
  download(projectId, format) {
    return request('GET', `/api/creation/download/${projectId}/`, {
      params: format ? { format } : undefined,
      responseType: 'blob',
    })
  },
  /** 生成作品分享链接 */
  share(projectId, options) {
    return request('POST', `/api/creation/${projectId}/share/`, { data: options || {} })
  },
  /** 通过分享 token 查看内容（公开接口） */
  shareView(token) {
    return request('GET', `/api/creation/share/view/${token}/`)
  },
  /** 通过分享 token 下载 */
  dlByToken(token, format) {
    return request('GET', `/api/creation/share/download/${token}/`, {
      params: format ? { format } : undefined,
      responseType: 'blob',
    })
  },
}

// ============================================================
//                          模块：works
// ============================================================
const works = {
  /** 作品列表，支持分页与状态过滤 */
  list(page, status) {
    return request('GET', '/api/works/', {
      params: { page: page || 1, status },
    })
  },
  /** 作品详情 */
  detail(projectId) {
    return request('GET', `/api/works/${projectId}/`)
  },
  /** 作品分享 */
  share(projectId, options) {
    return request('POST', `/api/works/${projectId}/share/`, { data: options || {} })
  },
  /** 作品统计（创作数、收藏、评分趋势等） */
  stats() {
    return request('GET', '/api/works/stats/')
  },
}

// ============================================================
//                         模块：skill（公共题材下拉）
// ============================================================
const skill = {
  themes() {
    return request('GET', '/api/skill/themes/public/')
  },
}

// ============================================================
//                            统一导出
// ============================================================
export { auth, users, membership, orders, creation, works, skill }

/**
 * 兼容老代码的命名导出（Member / Profile 页面仍在使用）：
 *   authApi / userApi / memberApi / orderApi / creationApi / worksApi / skillApi
 * 调用方式不变，但底层统一走新的 request 管道。
 */
export const authApi = auth
export const userApi = users
export const memberApi = membership
export const orderApi = orders
export const creationApi = creation
export const worksApi = works
export const skillApi = skill

/**
 * 分享页（公开接口，不需要登录）
 * 保持与老代码一致的命名
 */
export const shareApi = {
  view: (token) => creation.shareView(token),
  download: (token, format) => creation.dlByToken(token, format),
}

/**
 * 后台管理 API（保留原有结构，路径不变）
 * 同样走统一 request 管道，从而自动附带鉴权与响应解析
 */
export const adminApi = {
  getDashboard: () => request('GET', '/api/admin/dashboard/'),
  getUsers: (page = 1) => request('GET', '/api/admin/users/', { params: { page } }),
  toggleUserActive: (id) => request('POST', `/api/admin/users/${id}/toggle_active/`),
  resetUserPassword: (id) => request('POST', `/api/admin/users/${id}/reset_password/`),
  getSkillConfigs: () => request('GET', '/api/admin/skill/configs/'),
  updateSkillConfig: (key, value) =>
    request('PUT', `/api/admin/skill/configs/${key}/`, { data: { value } }),
  getThemes: () => request('GET', '/api/admin/skill/themes/'),
  addTheme: (data) => request('POST', '/api/admin/skill/themes/', { data }),
  updateTheme: (id, data) => request('PUT', `/api/admin/skill/themes/${id}/`, { data }),
  getHooks: () => request('GET', '/api/admin/skill/hooks/'),
  addHook: (data) => request('POST', '/api/admin/skill/hooks/', { data }),
  getOrders: (page = 1) => request('GET', '/api/admin/orders/', { params: { page } }),
  refundOrder: (id) => request('POST', `/api/admin/orders/${id}/refund/`),
  generatePromo: (data) =>
    request('POST', '/api/admin/members/codes/generate/', { data }),
}

/** 供外部直接使用 baseURL */
export const API_BASE = API_BASE_URL

/** 原始请求函数（供特殊场景使用，例如调用未规范化的接口） */
export const rawRequest = request

export default {
  auth,
  users,
  membership,
  orders,
  creation,
  works,
  skill,
  API_BASE,
}
