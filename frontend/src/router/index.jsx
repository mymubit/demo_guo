/**
 * router/index.jsx —— 路由配置（懒加载）
 *
 * 所有页面组件使用 React.lazy() 按需加载，降低首屏体积。
 * 公共骨架 Loading 由 Suspense fallback 统一提供。
 */
import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate, useSearchParams } from 'react-router-dom'
import MainLayout from '@/components/layout/MainLayout'
import AdminLayout from '@/components/layout/AdminLayout'
import AdminShell from '@/components/admin/AdminShell'
import { PrivateRoute, AdminRoute } from './guards'

// ---- C 端页面 ----
const Home = lazy(() => import('@/pages/Home'))
const Login = lazy(() => import('@/pages/Auth/Login'))
const Register = lazy(() => import('@/pages/Auth/Register'))
const Member = lazy(() => import('@/pages/Member'))
const Creation = lazy(() => import('@/pages/Creation'))
const ScriptEvaluate = lazy(() => import('@/pages/Tools/ScriptEvaluate'))
const PullSheetAnalyze = lazy(() => import('@/pages/Tools/PullSheetAnalyze'))
const Works = lazy(() => import('@/pages/Works'))
const WorksDetail = lazy(() => import('@/pages/Works/Detail'))
const Profile = lazy(() => import('@/pages/Profile'))
const Wallet = lazy(() => import('@/pages/Wallet'))
const ShareView = lazy(() => import('@/pages/Share'))
const NotFound = lazy(() => import('@/pages/NotFound'))

// ---- Admin 页面 ----
const AdminLogin = lazy(() => import('@/pages/Admin/Login'))
const AdminDashboard = lazy(() => import('@/pages/Admin/Dashboard'))
const MonitoringDashboardPage = lazy(() => import('@/pages/Admin/monitoring/MonitoringDashboardPage'))
const AdminUsers = lazy(() => import('@/pages/Admin/Users'))
const AdminOrders = lazy(() => import('@/pages/Admin/Orders'))
const AdminSettings = lazy(() => import('@/pages/Admin/Settings'))
const SystemConfigCenterPage = lazy(() => import('@/pages/Admin/system/SystemConfigCenterPage'))
const MainChainStudioPage = lazy(() => import('@/pages/Admin/mainChain/MainChainStudioPage'))
const AgentHubPage = lazy(() => import('@/pages/Admin/agent/AgentHubPage'))
const OrchestrationMonitor = lazy(() => import('@/pages/Admin/orchestration/OrchestrationMonitor'))
const ModelHubPage = lazy(() => import('@/pages/Admin/model/ModelHubPage'))
const PortalContentPage = lazy(() => import('@/pages/Admin/portal/PortalContentPage'))
const CreationProjectsPage = lazy(() => import('@/pages/Admin/CreationProjects'))
const CreationProjectTracePage = lazy(() => import('@/pages/Admin/CreationProjectTrace'))

// Admin 聚合页（内含多个子页面，变量名必须大写开头才能用作 JSX 组件）
const CreationCenterPage = lazy(() =>
  import('@/pages/Admin/CreationCenterPage').then((m) => ({ default: m.CreationCenterPage }))
)
const SystemAdvancedPage = lazy(() =>
  import('@/pages/Admin/SectionSettingsRoute').then((m) => ({ default: m.SystemAdvancedPage }))
)
const CommerceSettingsPage = lazy(() =>
  import('@/pages/Admin/CommerceSettingsRoute').then((m) => ({ default: m.CommerceSettingsPage }))
)
const MembersPlansPage = lazy(() =>
  import('@/pages/Admin/MemberSettingsRoute').then((m) => ({ default: m.MembersPlansPage }))
)

// ---- 旧路由重定向 ----
function PipelineLegacyRedirect() {
  const [searchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'models'
  const targets = {
    models: '/admin/model',
    steps: '/admin/main-chain',
    agents: '/admin/agent?tab=registry',
    rules: '/admin/agent?tab=rules',
    review: '/admin/agent?tab=review',
    assist: '/admin/portal?tab=ai-fields',
  }
  return <Navigate to={targets[tab] || '/admin/model'} replace />
}

function OrchestrationLegacyRedirect() {
  const [searchParams] = useSearchParams()
  const view = searchParams.get('view')
  const to = view ? `/admin/orchestration?view=${encodeURIComponent(view)}` : '/admin/orchestration'
  return <Navigate to={to} replace />
}

function PortalLegacyRedirect() {
  const [searchParams] = useSearchParams()
  const tab = searchParams.get('tab')
  const to = tab ? `/admin/portal?tab=${encodeURIComponent(tab)}` : '/admin/portal'
  return <Navigate to={to} replace />
}

function SystemSettingsPage() {
  return (
    <AdminShell>
      <Suspense fallback={null}>
        <AdminSettings />
      </Suspense>
    </AdminShell>
  )
}

const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[200px]">
    <div className="w-6 h-6 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
  </div>
)

export default function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/member"
            element={<PrivateRoute><Member /></PrivateRoute>}
          />
          <Route
            path="/creation"
            element={<PrivateRoute><Creation /></PrivateRoute>}
          />
          <Route
            path="/evaluate"
            element={<PrivateRoute><ScriptEvaluate /></PrivateRoute>}
          />
          <Route
            path="/pull-sheet"
            element={<PrivateRoute><PullSheetAnalyze /></PrivateRoute>}
          />
          <Route
            path="/works"
            element={<PrivateRoute><Works /></PrivateRoute>}
          />
          <Route
            path="/works/:id"
            element={<PrivateRoute><WorksDetail /></PrivateRoute>}
          />
          <Route
            path="/profile"
            element={<PrivateRoute><Profile /></PrivateRoute>}
          />
          <Route
            path="/wallet"
            element={<PrivateRoute><Wallet /></PrivateRoute>}
          />
          <Route path="/share/:token" element={<ShareView />} />
        </Route>

        <Route path="/admin/login" element={<AdminLogin />} />

        <Route
          path="/admin"
          element={<AdminRoute><AdminLayout /></AdminRoute>}
        >
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="monitoring" element={<MonitoringDashboardPage />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="orders" element={<AdminOrders />} />
          <Route path="members/plans" element={<MembersPlansPage />} />

          <Route path="creation" element={<CreationCenterPage />} />
          <Route path="creation/pipeline" element={<PipelineLegacyRedirect />} />
          <Route path="creation/content" element={<PortalLegacyRedirect />} />
          <Route path="creation/projects" element={<CreationProjectsPage />} />
          <Route path="creation/projects/:projectId/trace" element={<CreationProjectTracePage />} />
          <Route path="creation/agents" element={<OrchestrationLegacyRedirect />} />

          <Route path="main-chain" element={<MainChainStudioPage />} />
          <Route path="workflow" element={<Navigate to="/admin/main-chain" replace />} />
          <Route path="agent" element={<AgentHubPage />} />
          <Route path="orchestration" element={<OrchestrationMonitor />} />
          <Route path="model" element={<ModelHubPage />} />
          <Route path="portal" element={<PortalContentPage />} />

          <Route path="commerce/settings" element={<CommerceSettingsPage />} />

          <Route path="system" element={<SystemSettingsPage />} />
          <Route path="system/configs" element={<SystemConfigCenterPage />} />
          <Route path="system/advanced" element={<SystemAdvancedPage />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}
