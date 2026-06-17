/**
 * 短剧创作·设计体系 — 路由配置文件
 *
 * 【路由守卫策略】
 *   - Public：公开页面（Home / Login / 作品列表等）
 *   - Private：需登录（Creation / User Center / Orders / Wallet）
 *   - Admin：需登录 + 管理员权限
 *
 * 【路径命名约定】
 *   - /            → 首页
 *   - /creation    → 剧本创作中心（需登录）
 *   - /works       → 作品列表（替代 ScriptList）
 *   - /works/:id   → 作品详情
 *   - /profile     → 个人中心（需登录）
 *   - /member      → 会员中心（需登录）
 *   - /orders      → 我的订单（需登录）
 *   - /wallet      → 我的钱包（需登录）
 *   - /login       → 登录页
 *   - /register    → 注册页
 *   - /admin       → 管理后台（需管理员权限）
 *   - /*           → 404 兜底
 *
 * 【性能优化】
 *   - 全部页面采用 React.lazy + Suspense 进行懒加载
 *   - 由外层 SuspenseBoundary 统一处理加载态
 */

import { lazy, Suspense } from 'react'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { PrivateRoute, AdminRoute } from './guards.jsx'

// ── 布局组件 ────────────────────────────────────────────────
const MainLayout = lazy(() => import('@/components/layout/MainLayout.jsx'))
const AdminLayout = lazy(() => import('@/components/layout/AdminLayout.jsx'))

// ── 公开页面 ─────────────────────────────────────────────────
const Home = lazy(() => import('@/pages/Home/index.jsx'))
const WorkList = lazy(() => import('@/pages/Works/index.jsx'))
const WorkDetail = lazy(() => import('@/pages/Works/Detail.jsx'))
const Login = lazy(() => import('@/pages/Auth/Login.jsx'))
const Register = lazy(() => import('@/pages/Auth/Register.jsx'))

// ── 需登录页面 ───────────────────────────────────────────────
const CreationCenter = lazy(() => import('@/pages/Creation/index.jsx'))
const Profile = lazy(() => import('@/pages/Profile/index.jsx'))
const Member = lazy(() => import('@/pages/Member/index.jsx'))
const Orders = lazy(() => import('@/pages/Orders/index.jsx'))
const Wallet = lazy(() => import('@/pages/Wallet/index.jsx'))

// ── 管理后台 ─────────────────────────────────────────────────
const AdminDashboard = lazy(() => import('@/pages/Admin/Dashboard.jsx'))
const AdminProjects = lazy(() => import('@/pages/Admin/CreationProjects.jsx'))
const AdminSkills = lazy(() => import('@/pages/Admin/AdminSkills.jsx'))
const AdminUsers = lazy(() => import('@/pages/Admin/Users.jsx'))
const AdminOrders = lazy(() => import('@/pages/Admin/Orders.jsx'))
const AdminMembers = lazy(() => import('@/pages/Admin/Members.jsx'))
const AdminBilling = lazy(() => import('@/pages/Admin/Billing.jsx'))
const AdminSettings = lazy(() => import('@/pages/Admin/Settings.jsx'))
const AdminSystem = lazy(() => import('@/pages/Admin/AdminSystemConfig.jsx'))
const AdminLogin = lazy(() => import('@/pages/Admin/Login.jsx'))

// ── 【运营 F8】运营监控中心 ───────────────────────────────────
const OperationsDashboard = lazy(() => import('@/pages/Admin/operations/OperationsDashboardPage.jsx'))
const ContentQuality = lazy(() => import('@/pages/Admin/operations/ContentQualityPage.jsx'))
const OperationsFeedback = lazy(() => import('@/pages/Admin/operations/FeedbackPage.jsx'))
const ConfigEffectiveness = lazy(() => import('@/pages/Admin/operations/ConfigEffectivenessPage.jsx'))
const DailyChecklist = lazy(() => import('@/pages/Admin/operations/DailyChecklistPage.jsx'))

// ── 404 兜底 ─────────────────────────────────────────────────
const NotFound = lazy(() => import('@/pages/NotFound.jsx'))

/* ============================================================
 * Suspense 统一加载态 —— 避免每个 lazy 页面都重复写 loading
 * ============================================================ */
function PageLoading({ children }) {
  return (
    <Suspense
      fallback={
        <div className="min-h-[60vh] flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 rounded-full border-2 border-accent-400/30 border-t-accent-400 animate-spin" />
            <span className="text-sm text-navy-400">加载中...</span>
          </div>
        </div>
      }
    >
      {children}
    </Suspense>
  )
}

/* ============================================================
 * 路由表
 * ============================================================ */
const router = createBrowserRouter([
  // ── C 端主路由（带 MainLayout） ─────────────
  {
    element: (
      <PageLoading>
        <MainLayout />
      </PageLoading>
    ),
    children: [
      { path: '/', element: <Home /> },
      { path: '/works', element: <WorkList /> },
      { path: '/works/:id', element: <WorkDetail /> },

      // 需登录的页面
      {
        path: '/creation',
        element: (
          <PrivateRoute>
            <CreationCenter />
          </PrivateRoute>
        ),
      },
      {
        path: '/profile',
        element: (
          <PrivateRoute>
            <Profile />
          </PrivateRoute>
        ),
      },
      {
        path: '/member',
        element: (
          <PrivateRoute>
            <Member />
          </PrivateRoute>
        ),
      },
      {
        path: '/orders',
        element: (
          <PrivateRoute>
            <Orders />
          </PrivateRoute>
        ),
      },
      {
        path: '/wallet',
        element: (
          <PrivateRoute>
            <Wallet />
          </PrivateRoute>
        ),
      },
    ],
  },

  // ── Auth 路由（不带 MainLayout，避免重复嵌套） ──
  { path: '/login', element: <PageLoading><Login /></PageLoading> },
  { path: '/register', element: <PageLoading><Register /></PageLoading> },

  // ── 管理后台登录页（独立，避免重定向循环） ───
  { path: '/admin/login', element: <PageLoading><AdminLogin /></PageLoading> },

  // ── 管理后台（带 AdminLayout + AdminRoute） ──
  {
    path: '/admin',
    element: (
      <AdminRoute>
        <PageLoading>
          <AdminLayout />
        </PageLoading>
      </AdminRoute>
    ),
    children: [
      { index: true, element: <AdminDashboard /> },
      { path: 'dashboard', element: <AdminDashboard /> },
      { path: 'projects', element: <AdminProjects /> },
      { path: 'skills', element: <AdminSkills /> },
      { path: 'users', element: <AdminUsers /> },
      { path: 'orders', element: <AdminOrders /> },
      { path: 'members', element: <AdminMembers /> },
      { path: 'billing', element: <AdminBilling /> },
      { path: 'settings', element: <AdminSettings /> },
      { path: 'system', element: <AdminSystem /> },
      // 【运营 F8】运营监控中心
      { path: 'operations/dashboard', element: <OperationsDashboard /> },
      { path: 'operations/content-quality', element: <ContentQuality /> },
      { path: 'operations/feedback', element: <OperationsFeedback /> },
      { path: 'operations/config-hit', element: <ConfigEffectiveness /> },
      { path: 'operations/checklist', element: <DailyChecklist /> },
    ],
  },

  // ── 404 兜底 ─────────────────────────────────
  { path: '*', element: <PageLoading><NotFound /></PageLoading> },
])

export default function Router() {
  return <RouterProvider router={router} />
}
