import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

// API 基础配置
const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求签名 - 简化实现（生产环境使用 WebAssembly 执行）
function generateSignature(method, path, timestamp, nonce, body) {
  const secret = 'sf-client-sign-secret-change-in-production'
  const bodyHash = body ? JSON.stringify(body) : ''
  const signStr = `${method.toUpperCase()}${path}${timestamp}${nonce}${bodyHash}`
  // 简化签名（生产环境应由 WebAssembly 执行）
  let hash = 0
  for (let i = 0; i < signStr.length; i++) {
    const chr = signStr.charCodeAt(i)
    hash = ((hash << 5) - hash) + chr
    hash |= 0
  }
  return Math.abs(hash).toString(16) + secret.slice(0, 8)
}

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 签名 Header
    const timestamp = Math.floor(Date.now() / 1000)
    const nonce = Math.random().toString(36).substring(2, 18)
    config.headers['X-Timestamp'] = timestamp
    config.headers['X-Nonce'] = nonce
    config.headers['X-Signature'] = generateSignature(
      config.method,
      config.url,
      timestamp,
      nonce,
      config.data
    )
    config.headers['X-Device-Fingerprint'] = getDeviceFingerprint()

    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 直接返回响应数据
    return response.data
  },
  (error) => {
    const status = error.response?.status

    if (status === 401) {
      // 未授权，清除登录状态
      useAuthStore.getState().logout()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (status === 403) {
      console.error('权限不足')
    } else if (status === 429) {
      console.error('请求过于频繁，请稍后再试')
    }

    return Promise.reject(error.response?.data || error.message)
  }
)

// 设备指纹（简化版）
function getDeviceFingerprint() {
  const canvas = typeof document !== 'undefined' ? document.createElement('canvas') : null
  let fingerprint = 'unknown'
  if (canvas) {
    const ctx = canvas.getContext('2d')
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial'
    ctx.fillStyle = '#f60'
    ctx.fillText('fingerprint', 2, 2)
    fingerprint = canvas.toDataURL().slice(-32)
  }
  return fingerprint
}

// ============ API 方法 ============

// 认证
export const authApi = {
  login: (data) => api.post('/auth/login/', data),
  register: (data) => api.post('/auth/register/', data),
  refresh: (refresh) => api.post('/auth/refresh/', { refresh }),
  logout: () => api.post('/auth/logout/'),
}

// 用户
export const userApi = {
  getProfile: () => api.get('/users/me/'),
  updateProfile: (data) => api.put('/users/me/update/', data),
}

// 会员
export const memberApi = {
  getPlans: () => api.get('/members/plans/'),
  getMyMembership: () => api.get('/members/me/'),
  redeemCode: (code) => api.post('/members/redeem/', { code }),
}

// 订单
export const orderApi = {
  create: (planId) => api.post('/orders/create/', { plan_id: planId }),
  mockPay: (orderNo) => api.post('/orders/mock_pay/', { order_no: orderNo }),
  list: () => api.get('/orders/'),
}

// 创作
export const creationApi = {
  submit: (data) => api.post('/creation/submit/', data),
  getProgress: (taskId) => api.get(`/creation/progress/${taskId}/`),
  download: (projectId) => api.get(`/creation/download/${projectId}/`, { responseType: 'blob' }),
}

// 作品
export const worksApi = {
  list: (page = 1) => api.get(`/works/?page=${page}`),
  getDetail: (id) => api.get(`/works/${id}/`),
}

// 后台管理
export const adminApi = {
  getDashboard: () => api.get('/admin/dashboard/'),
  getUsers: (page = 1) => api.get(`/admin/users/?page=${page}`),
  toggleUserActive: (id) => api.post(`/admin/users/${id}/toggle_active/`),
  resetUserPassword: (id) => api.post(`/admin/users/${id}/reset_password/`),
  getSkillConfigs: () => api.get('/admin/skill/configs/'),
  updateSkillConfig: (key, value) => api.put(`/admin/skill/configs/${key}/`, { value }),
  getThemes: () => api.get('/admin/skill/themes/'),
  addTheme: (data) => api.post('/admin/skill/themes/', data),
  updateTheme: (id, data) => api.put(`/admin/skill/themes/${id}/`, data),
  getHooks: () => api.get('/admin/skill/hooks/'),
  addHook: (data) => api.post('/admin/skill/hooks/', data),
  getOrders: (page = 1) => api.get(`/admin/orders/?page=${page}`),
  refundOrder: (id) => api.post(`/admin/orders/${id}/refund/`),
  generatePromo: (data) => api.post('/admin/members/codes/generate/', data),
}

export default api
