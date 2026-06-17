// 设计体系 · 组件导出索引
//
// 目录规范:
// components/ui/          基础组件 — 原子/通用
// components/admin/       管理后台组件 — 与 AdminShell 对齐
// components/creation/    创作侧专用组件
//
// 新增组件: 必须在对应目录和此处导出, 并编写规范注释

// -------- 基础组件 --------
export { default as Button } from '@/components/ui/Button.jsx'
export { default as Badge } from '@/components/ui/Badge.jsx'
export { default as EmptyState, EmptyStateWithButton } from '@/components/ui/EmptyState.jsx'
export { default as SkeletonBlock, SkeletonLines, SkeletonCard, SkeletonTableRow, SkeletonPage } from '@/components/ui/Skeleton.jsx'

// -------- 管理后台组件 (模块4) --------
export { default as AdminShell } from '@/components/admin/AdminShell.jsx'
export { AdminToolbar, AdminToolbarGroup, AdminToolbarActions, AdminTable, AdminPanel, AdminPagination, AdminKpiCard } from '@/components/admin/AdminShell.jsx'
