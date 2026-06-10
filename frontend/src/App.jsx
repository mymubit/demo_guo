import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from '@/components/layout/MainLayout'
import AdminLayout from '@/components/layout/AdminLayout'
import Home from '@/pages/Home'
import Login from '@/pages/Auth/Login'
import Register from '@/pages/Auth/Register'
import Member from '@/pages/Member'
import Creation from '@/pages/Creation'
import Works from '@/pages/Works'
import WorksDetail from '@/pages/Works/Detail'
import Profile from '@/pages/Profile'
import AdminLogin from '@/pages/Admin/Login'
import AdminDashboard from '@/pages/Admin/Dashboard'
import AdminUsers from '@/pages/Admin/Users'
import AdminMembers from '@/pages/Admin/Members'
import AdminSkillConfig from '@/pages/Admin/SkillConfig'
import AdminOrders from '@/pages/Admin/Orders'
import ShareView from '@/pages/ShareView'
import NotFound from '@/pages/NotFound'

// 路由守卫
const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('scriptforge-auth')
  const hasAuth = token ? true : false
  if (!hasAuth) {
    return <Navigate to="/login" replace />
  }
  return children
}

const AdminRoute = ({ children }) => {
  // 简化的管理员检查
  const token = localStorage.getItem('scriptforge-auth')
  const userData = localStorage.getItem('scriptforge-auth')
  const hasAuth = token ? true : false
  // 实际项目中应检查 user.is_staff / is_superuser
  const isAdmin = userData && (userData.includes('is_staff') || userData.includes('is_superuser')) || hasAuth
  if (!hasAuth) {
    return <Navigate to="/admin/login" replace />
  }
  return children
}

export default function App() {
  return (
    <Routes>
      {/* 主站 */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/member"
          element={
            <PrivateRoute>
              <Member />
            </PrivateRoute>
          }
        />
        <Route
          path="/creation"
          element={
            <PrivateRoute>
              <Creation />
            </PrivateRoute>
          }
        />
        <Route
          path="/works"
          element={
            <PrivateRoute>
              <Works />
            </PrivateRoute>
          }
        />
        <Route
          path="/works/:id"
          element={
            <PrivateRoute>
              <WorksDetail />
            </PrivateRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <PrivateRoute>
              <Profile />
            </PrivateRoute>
          }
        />
        <Route path="/share/:token" element={<ShareView />} />
      </Route>

      {/* 后台管理 */}
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminLayout />
          </AdminRoute>
        }
      >
        <Route index element={<Navigate to="/admin/dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboard />} />
        <Route path="users" element={<AdminUsers />} />
        <Route path="members" element={<AdminMembers />} />
        <Route path="skill-config" element={<AdminSkillConfig />} />
        <Route path="orders" element={<AdminOrders />} />
      </Route>

      {/* 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
