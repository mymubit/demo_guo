/**
 * router/guards.jsx —— 路由权限守卫
 *
 * PrivateRoute：需要登录，未登录跳转 /login
 * AdminRoute：需要登录 + 管理员权限，无权跳转 /admin/login
 */
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

export function PrivateRoute({ children }) {
  const { token } = useAuthStore()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

export function AdminRoute({ children }) {
  const { token, isAuthenticated, hasAdminAccess } = useAuthStore()
  const hasAuth = Boolean(isAuthenticated || token)
  const isAdmin = hasAdminAccess()

  if (!hasAuth) {
    return <Navigate to="/admin/login" replace />
  }
  if (!isAdmin) {
    return <Navigate to="/admin/login" replace state={{ error: '无管理权限' }} />
  }
  return children
}
