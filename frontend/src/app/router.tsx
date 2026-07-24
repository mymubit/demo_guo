import { type ComponentType } from 'react'
import {
  BarChart3,
  BookOpen,
  ClipboardCheck,
  CreditCard,
  LayoutDashboard,
  Library,
  ScrollText,
  Settings2,
  Sparkles,
} from 'lucide-react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '@/router/ProtectedRoute'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { TemplatesPage } from '@/pages/TemplatesPage'
import { KnowledgePage } from '@/pages/KnowledgePage'
import { ModelsPage } from '@/pages/ModelsPage'
import { LogsPage } from '@/pages/LogsPage'
import { UsagePage } from '@/pages/UsagePage'
import { SystemPage } from '@/pages/SystemPage'
import { BillingPage } from '@/pages/BillingPage'
import { ScriptReviewsPage } from '@/pages/ScriptReviewsPage'
import { ScriptReviewNewPage } from '@/pages/ScriptReviewNewPage'
import { ScriptReviewDetailPage } from '@/pages/ScriptReviewDetailPage'
import { ScriptReviewComparePage } from '@/pages/ScriptReviewComparePage'
import { ProjectOverviewPage } from '@/pages/ProjectOverviewPage'
import { TopicPage } from '@/pages/TopicPage'
import { BlueprintPage } from '@/pages/BlueprintPage'
import { EpisodesPage } from '@/pages/EpisodesPage'
import { ScriptEditorPage } from '@/pages/ScriptEditorPage'
import { QualityPage } from '@/pages/QualityPage'
import { DeliveryPage } from '@/pages/DeliveryPage'
import {
  ProjectStageRedirect,
  ProjectWorkbenchLayout,
} from '@/pages/ProjectWorkbenchLayout'
import { AppShell } from './AppShell'

export type V3NavItem = {
  to: string
  label: string
  hint: string
  icon: ComponentType<{ className?: string }>
}

/** V3 全局一级导航（path + label + hint + icon 单一来源） */
export const V3_NAV_ITEMS: V3NavItem[] = [
  { to: '/dashboard', label: '创作仪表盘', hint: '项目与创作进度', icon: LayoutDashboard },
  { to: '/reviews', label: '剧本评审', hint: '外界剧本评分与对比', icon: ClipboardCheck },
  { to: '/templates', label: '模板库', hint: '内置与自定义模板', icon: Library },
  { to: '/knowledge', label: '知识库', hint: '创作知识文档', icon: BookOpen },
  { to: '/models', label: '模型配置', hint: '供应商与运行参数', icon: Sparkles },
  { to: '/logs', label: '执行日志', hint: '生成与调用记录', icon: ScrollText },
  { to: '/usage', label: '用量', hint: 'Token 与费用', icon: BarChart3 },
  { to: '/system', label: '系统配置', hint: '工作空间偏好', icon: Settings2 },
  { to: '/billing', label: '套餐', hint: '方案与权益', icon: CreditCard },
]

/** V3 全局一级导航路径（不含项目内路由） */
export const V3_NAV_PATHS = V3_NAV_ITEMS.map((item) => item.to) as readonly string[]

export function V3Routes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/reviews" element={<ScriptReviewsPage />} />
          <Route path="/reviews/new" element={<ScriptReviewNewPage />} />
          <Route path="/reviews/:id" element={<ScriptReviewDetailPage />} />
          <Route path="/reviews/:id/compare" element={<ScriptReviewComparePage />} />
          <Route path="/templates" element={<TemplatesPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/usage" element={<UsagePage />} />
          <Route path="/system" element={<SystemPage />} />
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/projects/:id" element={<ProjectWorkbenchLayout />}>
            <Route index element={<ProjectStageRedirect />} />
            <Route path="settings" element={<ProjectOverviewPage />} />
            <Route path="topic" element={<TopicPage />} />
            <Route path="blueprint" element={<BlueprintPage />} />
            <Route path="episodes" element={<EpisodesPage />} />
            <Route path="editor" element={<ScriptEditorPage />} />
            <Route path="quality" element={<QualityPage />} />
            <Route path="delivery" element={<DeliveryPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
