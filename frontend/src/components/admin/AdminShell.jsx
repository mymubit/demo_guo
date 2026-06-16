// 管理后台统一壳组件 — 所有 admin/* 页面必须使用此壳
//
// 设计规范 (模块4):
// 1. 页面标题区 — 大标题 + 描述 + 右侧操作按钮
// 2. 工具栏区 — 筛选/搜索/批量操作
// 3. 面包屑 — 层级导航
// 4. 响应式 — 工具栏在窄屏折叠,表格横向滚动
//
// 用法:
//   <AdminShell
//     title="技能管理"
//     description="管理短剧创作技能"
//     breadcrumbs={[{ label: '创作中心', href: '/admin/creation' }]}
//     actions={<Button variant="brand">新建技能</Button>}
//     toolbar={
//       <AdminToolbar>
//         <input placeholder="搜索..." />
//         <select>筛选</select>
//       </AdminToolbar>
//     }
//   >
//     <AdminTable ... />
//   </AdminShell>

import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Link } from 'react-router-dom'

// ---------- AdminShell 主壳 ----------

export default function AdminShell({
  title,
  description,
  breadcrumbs,
  actions,
  toolbar,
  children,
  className,
  noPadding = false,
}) {
  return (
    <div className={cn('min-h-screen pb-20', className)}>
      {/* 标题区 */}
      <div className="mb-6 animate-fade-in">
        {/* 面包屑 — 可选 */}
        {breadcrumbs && breadcrumbs.length > 0 && (
          <div className="flex items-center gap-1 mb-3 text-sm text-slate-400">
            {breadcrumbs.map((item, idx) => (
              <span key={idx} className="flex items-center gap-1">
                {idx > 0 && <ChevronRight className="w-4 h-4" />}
                {item.href ? (
                  <Link
                    to={item.href}
                    className="hover:text-white transition-colors"
                  >
                    {item.label}
                  </Link>
                ) : (
                  <span className={idx === breadcrumbs.length - 1 ? 'text-slate-200' : ''}>
                    {item.label}
                  </span>
                )}
              </span>
            ))}
            <ChevronRight className="w-4 h-4" />
            <span className="text-slate-200">{title}</span>
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div>
            {title && (
              <h1 className="text-2xl font-bold text-white tracking-tight">{title}</h1>
            )}
            {description && (
              <p className="text-sm text-slate-400 mt-1 max-w-2xl">{description}</p>
            )}
          </div>
          {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
        </div>
      </div>

      {/* 工具栏区 — 可选 */}
      {toolbar && (
        <div className="mb-5 rounded-2xl border border-white/5 bg-slate-900/60 p-4 animate-fade-in">
          {toolbar}
        </div>
      )}

      {/* 主体内容区 */}
      <div className={cn('animate-fade-in', noPadding ? '' : '')}>{children}</div>
    </div>
  )
}

// ---------- AdminToolbar 工具栏容器 ----------
// 规范: flex + 自动换行,左侧是筛选/搜索,右侧是批量操作

export function AdminToolbar({ children, className, rightAligned }) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-2',
        rightAligned ? 'justify-end' : 'justify-between',
        className,
      )}
    >
      {children}
    </div>
  )
}

// 工具栏左分组 — 搜索/筛选
export function AdminToolbarGroup({ children, className }) {
  return <div className={cn('flex flex-wrap items-center gap-2', className)}>{children}</div>
}

// 工具栏右分组 — 批量操作
export function AdminToolbarActions({ children, className }) {
  return <div className={cn('flex flex-wrap items-center gap-2', className)}>{children}</div>
}

// ---------- AdminTable 表格 ----------
// 合并原 AdminPrimitives 和 AdminUI 中的重复实现

export function AdminTable({
  columns,
  rows,
  rowKey = 'id',
  isLoading = false,
  emptyText = '暂无数据',
  emptyAction,
  onRowClick,
  rowClassName,
  dense = false,
  highlightRows,
}) {
  if (isLoading) {
    return <AdminTableSkeleton columns={columns?.length || 3} dense={dense} />
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="rounded-2xl border border-white/5 bg-slate-900/60">
        <div className={cn('py-12', !emptyAction && 'py-8')}>
          <AdminEmptyInline
            text={emptyText}
            action={emptyAction}
            compact={!emptyAction}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/60 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/5 text-slate-400 text-left">
              {columns?.map((col, idx) => (
                <th
                  key={col.key || `col-${idx}`}
                  className={cn(
                    'font-medium',
                    dense ? 'px-3 py-2' : 'px-4 py-3',
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center',
                    col.className,
                  )}
                  style={col.width ? { width: col.width } : undefined}
                >
                  {col.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIdx) => (
              <tr
                key={row[rowKey] || rowIdx}
                onClick={onRowClick ? () => onRowClick(row, rowIdx) : undefined}
                className={cn(
                  'border-b border-white/5 transition-colors',
                  onRowClick && 'hover:bg-slate-800/40 cursor-pointer',
                  highlightRows?.(row, rowIdx) ? 'bg-accent/5' : '',
                  rowClassName?.(row, rowIdx),
                )}
              >
                {columns?.map((col, colIdx) => (
                  <td
                    key={col.key || `cell-${colIdx}`}
                    className={cn(
                      dense ? 'px-3 py-2' : 'px-4 py-3',
                      col.align === 'right' && 'text-right',
                      col.align === 'center' && 'text-center',
                      col.cellClassName,
                    )}
                  >
                    {col.render ? col.render(row, rowIdx) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// 表格骨架
function AdminTableSkeleton({ columns = 3, dense = false }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/60 overflow-hidden">
      <div className={cn('border-b border-white/5', dense ? 'py-2' : 'py-3', 'px-4 text-slate-400 text-sm')}>
        {Array.from({ length: columns }).map((_, i) => (
          <span key={i} className="inline-block mr-8 h-2 w-16 rounded bg-slate-800/60" />
        ))}
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'flex gap-3 items-center border-b border-white/5 animate-pulse',
            dense ? 'py-2' : 'py-3',
            'px-4',
          )}
        >
          {Array.from({ length: columns }).map((_, j) => (
            <div key={j} className="h-3 flex-1 rounded bg-slate-800/50" />
          ))}
        </div>
      ))}
    </div>
  )
}

// 表格内联空状态
function AdminEmptyInline({ text, action, compact = false }) {
  return (
    <div className={cn('flex flex-col items-center justify-center text-center', compact ? 'py-6' : 'py-12')}>
      <div className={cn('rounded-2xl bg-slate-800/60 flex items-center justify-center mb-3', compact ? 'w-10 h-10' : 'w-14 h-14')}>
        <div className={cn('text-slate-500', compact ? 'w-5 h-5' : 'w-7 h-7')}>📭</div>
      </div>
      <h3 className={cn('font-semibold text-white mb-1', compact ? 'text-sm' : 'text-base')}>{text}</h3>
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}

// ---------- AdminPagination 分页 ----------

export function AdminPagination({
  page = 1,
  pageSize = 10,
  total = 0,
  onChange,
}) {
  const totalPages = Math.ceil(total / pageSize) || 1
  const hasPrev = page > 1
  const hasNext = page < totalPages

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-4 text-sm">
      <div className="text-slate-400">
        共 <span className="text-slate-200 font-medium">{total}</span> 条 · 第{' '}
        <span className="text-slate-200 font-medium">{page}</span> /{' '}
        <span className="text-slate-200 font-medium">{totalPages}</span> 页
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => hasPrev && onChange(page - 1)}
          disabled={!hasPrev}
          className={cn(
            'h-8 w-8 rounded-lg flex items-center justify-center transition-colors',
            hasPrev
              ? 'border border-white/10 bg-slate-800/70 text-slate-200 hover:bg-slate-700/70'
              : 'bg-slate-800/30 text-slate-500 cursor-not-allowed',
          )}
          aria-label="上一页"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <div className="flex items-center gap-1 px-2">
          <span className="text-slate-300 min-w-[60px] text-center">{page}</span>
        </div>
        <button
          onClick={() => hasNext && onChange(page + 1)}
          disabled={!hasNext}
          className={cn(
            'h-8 w-8 rounded-lg flex items-center justify-center transition-colors',
            hasNext
              ? 'border border-white/10 bg-slate-800/70 text-slate-200 hover:bg-slate-700/70'
              : 'bg-slate-800/30 text-slate-500 cursor-not-allowed',
          )}
          aria-label="下一页"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

// ---------- AdminPanel 信息面板 ----------

export function AdminPanel({ title, children, action, className }) {
  return (
    <div className={cn('rounded-2xl border border-white/5 bg-slate-900/60', className)}>
      {(title || action) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
          {title && <h2 className="text-base font-semibold text-white">{title}</h2>}
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  )
}

// ---------- AdminKpi KPI 卡片 ----------

export function AdminKpiCard({
  title,
  value,
  trend,
  trendLabel,
  icon,
  variant = 'default',
  onClick,
}) {
  const variants = {
    default: 'bg-slate-900/60 border-white/5',
    brand: 'bg-brand-500/10 border-brand-500/20',
    accent: 'bg-accent-400/10 border-accent-400/20',
    success: 'bg-success-bg border-success-border',
    danger: 'bg-danger-bg border-danger-border',
  }

  return (
    <div
      className={cn(
        'rounded-2xl border p-5 transition-all',
        variants[variant] || variants.default,
        onClick && 'hover:bg-slate-900/80 cursor-pointer',
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm text-slate-400">{title}</span>
        {icon && <div className="text-slate-500">{icon}</div>}
      </div>
      <div className="text-2xl font-bold text-white mb-2">{value}</div>
      {trend !== undefined && (
        <div
          className={cn(
            'text-xs flex items-center gap-1',
            trend >= 0 ? 'text-success-light' : 'text-danger-light',
          )}
        >
          <span>{trend >= 0 ? '↑' : '↓'}</span>
          <span>{trendLabel || `${Math.abs(trend)}%`}</span>
        </div>
      )}
    </div>
  )
}
