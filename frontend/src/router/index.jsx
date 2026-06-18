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
 *   - /evaluate    → 剧本评估（需登录）
 *   - /pull-sheet  → 拉片分析（需登录）
 *   - /share/:token → 作品分享预览（公开）
 *   - /tools       → 重定向至 /evaluate
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
import { createBrowserRouter, RouterProvider, Outlet, Navigate, useParams, useLocation } from 'react-router-dom'
import { PrivateRoute, AdminRoute } from './guards.jsx'
import { MonitorRouteTracker } from '@/utils/monitor'

/** 懒加载具名导出页面 */
function lazyNamed(importFn, exportName) {
  return lazy(() => importFn().then((mod) => ({ default: mod[exportName] })))
}

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
const ScriptEvaluate = lazy(() => import('@/pages/Tools/ScriptEvaluate.jsx'))
const PullSheetAnalyze = lazy(() => import('@/pages/Tools/PullSheetAnalyze.jsx'))
const ShareView = lazy(() => import('@/pages/Share/index.jsx'))

// ── 管理后台 ─────────────────────────────────────────────────
const AdminDashboard = lazy(() => import('@/pages/Admin/Dashboard.jsx'))
const AdminStats = lazy(() => import('@/pages/Admin/AdminStats.jsx'))
const AdminMonitoring = lazy(() => import('@/pages/Admin/monitoring/MonitoringDashboardPage.jsx'))
const AdminProjects = lazy(() => import('@/pages/Admin/CreationProjects.jsx'))
const AdminProjectTrace = lazy(() => import('@/pages/Admin/CreationProjectTrace.jsx'))

function AdminProjectTraceLegacyRedirect() {
  const { projectId } = useParams()
  const { search } = useLocation()
  return <Navigate to={`/admin/creation/projects/${projectId}${search || ''}`} replace />
}
const AdminModelHub = lazy(() => import('@/pages/Admin/model/ModelHubPage.jsx'))
const AdminAgentHub = lazy(() => import('@/pages/Admin/agent/AgentHubPage.jsx'))
const SkillCenterPage = lazy(() => import('@/pages/Admin/skills/SkillCenterPage.jsx'))
const AdminLibrary = lazy(() => import('@/pages/Admin/library/AdminLibrary.jsx'))
const AdminEvolution = lazy(() => import('@/pages/Admin/evolution/AdminEvolution.jsx'))
const AdminUsers = lazy(() => import('@/pages/Admin/Users.jsx'))
const AdminOrders = lazy(() => import('@/pages/Admin/Orders.jsx'))
const AdminMembers = lazy(() => import('@/pages/Admin/Members.jsx'))
const MembersPlansPage = lazyNamed(() => import('@/pages/Admin/MemberSettingsRoute.jsx'), 'MembersPlansPage')
const AdminBilling = lazy(() => import('@/pages/Admin/Billing.jsx'))
const CommerceSettingsPage = lazyNamed(() => import('@/pages/Admin/CommerceSettingsRoute.jsx'), 'CommerceSettingsPage')
const AdminPortal = lazy(() => import('@/pages/Admin/portal/PortalContentPage.jsx'))
const AdminSettings = lazy(() => import('@/pages/Admin/Settings.jsx'))
const AdminSystem = lazy(() => import('@/pages/Admin/AdminSystemConfig.jsx'))
const SystemConfigCenter = lazy(() => import('@/pages/Admin/system/SystemConfigCenterPage.jsx'))
const SystemAdvancedPage = lazyNamed(() => import('@/pages/Admin/SectionSettingsRoute.jsx'), 'SystemAdvancedPage')
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

function RootLayout() {
  return (
    <>
      <MonitorRouteTracker />
      <Outlet />
    </>
  )
}

/* ============================================================
 * 路由表
 * ============================================================ */
const appRoutes = [
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
      {
        path: '/evaluate',
        element: (
          <PrivateRoute>
            <ScriptEvaluate />
          </PrivateRoute>
        ),
      },
      {
        path: '/pull-sheet',
        element: (
          <PrivateRoute>
            <PullSheetAnalyze />
          </PrivateRoute>
        ),
      },
    ],
  },

  // ── Auth 路由（不带 MainLayout，避免重复嵌套） ──
  { path: '/login', element: <PageLoading><Login /></PageLoading> },
  { path: '/register', element: <PageLoading><Register /></PageLoading> },

  // ── 公开分享（独立布局，无顶栏） ──
  { path: '/share/:token', element: <PageLoading><ShareView /></PageLoading> },

  // ── 兼容别名 ──
  { path: '/tools', element: <Navigate to="/evaluate" replace /> },
  { path: '/tools/evaluate', element: <Navigate to="/evaluate" replace /> },
  { path: '/tools/pull-sheet', element: <Navigate to="/pull-sheet" replace /> },

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
      { index: true, element: <Navigate to="dashboard" replace /> },
      { path: 'dashboard', element: <AdminDashboard /> },
      // 概览
      { path: 'stats', element: <AdminStats /> },
      { path: 'monitoring', element: <AdminMonitoring /> },
      // 创作
      { path: 'creation', element: <Navigate to="/admin/creation/projects" replace /> },
      { path: 'creation/projects', element: <AdminProjects /> },
      { path: 'creation/projects/:projectId', element: <AdminProjectTrace /> },
      { path: 'creation/projects/:projectId/trace', element: <AdminProjectTraceLegacyRedirect /> },
      { path: 'projects', element: <AdminProjects /> },
      // AI 引擎
      { path: 'model', element: <AdminModelHub /> },
      { path: 'agent', element: <AdminAgentHub /> },
      { path: 'skills', element: <SkillCenterPage /> },
      { path: 'library', element: <AdminLibrary /> },
      { path: 'evolution', element: <AdminEvolution /> },
      // 用户与商业
      { path: 'users', element: <AdminUsers /> },
      { path: 'orders', element: <AdminOrders /> },
      { path: 'members', element: <AdminMembers /> },
      { path: 'members/plans', element: <MembersPlansPage /> },
      { path: 'billing', element: <AdminBilling /> },
      { path: 'commerce/settings', element: <CommerceSettingsPage /> },
      // 站点 / 系统
      { path: 'portal', element: <AdminPortal /> },
      { path: 'settings', element: <AdminSettings /> },
      { path: 'system', element: <AdminSystem /> },
      { path: 'system/maintenance', element: <AdminSettings /> },
      { path: 'system/configs', element: <SystemConfigCenter /> },
      { path: 'system/advanced', element: <SystemAdvancedPage /> },
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
]

const router = createBrowserRouter(
  [
    {
      element: <RootLayout />,
      children: appRoutes,
    },
  ],
  {
    future: {
      v7_startTransition: true,
    },
  },
)

export default function Router() {
  return <RouterProvider router={router} />
}
