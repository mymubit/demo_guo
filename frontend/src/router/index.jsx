// 短剧创作·设计体系 — 路由配置文件

import { lazy } from 'react'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'

// 页面懒加载 — 按需加载

// 基础页面
const Home = lazy(() => import('@/pages/Home.jsx'))
const CreationCenter = lazy(() => import('@/pages/CreationCenter.jsx'))
const WorkflowOrchestration = lazy(() => import('@/pages/WorkflowOrchestration.jsx'))
const ScriptList = lazy(() => import('@/pages/ScriptList.jsx'))
const ScriptDetail = lazy(() => import('@/pages/ScriptDetail.jsx'))
const ProjectDetail = lazy(() => import('@/pages/ProjectDetail.jsx'))
const UserCenter = lazy(() => import('@/pages/UserCenter.jsx'))
const NotFound = lazy(() => import('@/pages/NotFound.jsx'))

// 后台管理页面 — 设计规范: 所有 admin 页面必须使用统一的 AdminShell
const AdminLayout = lazy(() => import('@/pages/Admin/AdminLayout.jsx'))
const AdminOverview = lazy(() => import('@/pages/Admin/AdminOverview.jsx'))
const AdminSkills = lazy(() => import('@/pages/Admin/AdminSkills.jsx'))
const AdminProjects = lazy(() => import('@/pages/Admin/AdminProjects.jsx'))

const router = createBrowserRouter([
  {
    path: '/',
    element: <Home />,
  },
  {
    path: '/creation',
    element: <CreationCenter />,
  },
  {
    path: '/scripts',
    element: <ScriptList />,
  },
  {
    path: '/scripts/:id',
    element: <ScriptDetail />,
  },
  {
    path: '/projects/:id',
    element: <ProjectDetail />,
  },
  {
    path: '/workflow',
    element: <WorkflowOrchestration />,
  },
  {
    path: '/user',
    element: <UserCenter />,
  },
  // ============ 管理后台 ============
  {
    path: '/admin',
    element: <AdminLayout />,
    children: [
      { index: true, element: <AdminOverview /> },
      { path: 'skills', element: <AdminSkills /> },
      { path: 'projects', element: <AdminProjects /> },
    ],
  },
  // 404
  { path: '*', element: <NotFound /> },
])

export default function Router() {
  return <RouterProvider router={router} />
}
