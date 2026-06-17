/**
 * 管理后台页面壳组件 — ScriptForge 设计体系标准
 *
 * 【角色定位】
 * 本组件是所有 /admin/* 页面内容级的统一外层。
 * 不包含侧边栏/顶栏/面包屑（这部分由布局层 AdminLayout 统一处理），
 * 专注于：
 *   1) 页面标题 + 描述 + 右侧操作区
 *   2) 顶部工具栏（筛选/搜索/批量操作）
 *   3) 页面内容主区
 *   4) 可选的错误兜底/加载态
 *
 * 【组件层级】
 *   /components/layout/AdminLayout.jsx  ← 侧边栏 + 顶栏 + 面包屑
 *     └─ <AdminShell />                  ← 页面标题 + 工具栏 + 内容区
 *          ├─ AdminPageHeader / AdminPanel / AdminDataTable  (来自 AdminPrimitives)
 *          └─ AdminToolbar / AdminTabBar / AdminMessage       (来自 AdminUI)
 *
 * 【使用示例】
 *   import AdminShell from '@/components/admin/AdminShell'
 *   import { Button } from '@/components/ui'
 *
 *   <AdminShell
 *     title="技能管理"
 *     description="查看、创建和管理短剧创作技能"
 *     actions={<Button variant="brand">新建技能</Button>}
 *     toolbar={<AdminToolbar>...</AdminToolbar>}
 *   >
 *     <div>页面正文</div>
 *   </AdminShell>
 *
 * 【设计令牌对齐】
 *   - 背景色: slate-900/60（与主体一致）
 *   - 标题: text-2xl + font-bold + text-white
 *   - 描述: text-sm + text-slate-400
 *   - 内边距: p-6 lg:p-9（来自 AdminLayout）
 *   - 间距: header 与 content 之间 mb-5
 *
 */

import { cn } from '@/utils/cn'

export default function AdminShell({
  title,
  description,
  subtitle,
  actions,
  toolbar,
  headerActions,
  children,
  className,
  compact = false,
}) {
  const hasTitle = Boolean(title)
  const hasToolbar = Boolean(toolbar)
  const hasActions = Boolean(actions) || Boolean(headerActions)

  return (
    <div className={cn('space-y-5', className)}>
      {/* 页头：标题 + 描述 + 操作按钮 */}
      {(hasTitle || hasActions) && (
        <div
          className={cn(
            'flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4',
            compact && 'gap-3',
          )}
        >
          <div className="min-w-0">
            {title && (
              <h1
                className={cn(
                  'font-bold tracking-tight text-white',
                  compact ? 'text-lg' : 'text-2xl',
                )}
              >
                {title}
              </h1>
            )}
            {(description || subtitle) && (
              <p
                className={cn(
                  'text-slate-400 leading-relaxed mt-1 max-w-3xl',
                  compact ? 'text-xs' : 'text-sm',
                )}
              >
                {description || subtitle}
              </p>
            )}
          </div>
          {hasActions && (
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {headerActions || actions}
            </div>
          )}
        </div>
      )}

      {/* 工具栏：筛选/搜索/批量操作 */}
      {hasToolbar && (
        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-3.5 animate-fade-in">
          {toolbar}
        </div>
      )}

      {/* 内容主区 */}
      {children && <div className="animate-fade-in">{children}</div>}
    </div>
  )
}

/**
 * 内联空状态 — 用于表格无数据时
 * 与 @/components/ui/EmptyState.jsx 的区别：样式更贴合后台表格场景
 */
export function AdminEmptyInline({ title = '暂无数据', action, compact = false }) {
  return (
    <div className={cn('flex flex-col items-center justify-center text-center py-8', !compact && 'py-12')}>
      <div className="w-10 h-10 rounded-xl bg-slate-800/60 flex items-center justify-center mb-3 text-slate-500">
        <span className="text-lg">📭</span>
      </div>
      <h3 className="text-sm font-semibold text-white mb-1">{title}</h3>
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

/**
 * 加载骨架条 — 用于列表/表格加载时展示
 * 比 SkeletonBlock 更轻量，适合在单行内容位置使用
 */
export function AdminSkeletonRow({ count = 5 }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="h-10 rounded-lg bg-slate-800/50 animate-pulse"
          style={{ width: `${80 - (i * 4) % 30}%` }}
        />
      ))}
    </div>
  )
}
