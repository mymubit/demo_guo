/**
 * C 端章节标题与通用布局 primitive
 */
import { Search } from 'lucide-react'
import { cn } from '@/utils/cn'

export function SectionEyebrow({ children, className }) {
  return (
    <span
      className={cn(
        'text-xs uppercase tracking-[0.18em] text-gold-400 before:mr-2 before:inline-block before:h-px before:w-6 before:align-middle before:bg-gold-400',
        className,
      )}
    >
      {children}
    </span>
  )
}

export function SectionHeader({ eyebrow, title, subtitle, align = 'left', className }) {
  const centered = align === 'center'
  return (
    <header className={cn(centered && 'mx-auto max-w-2xl text-center', className)}>
      {eyebrow ? <SectionEyebrow>{eyebrow}</SectionEyebrow> : null}
      {title ? (
        <h1
          className={cn(
            'mt-3 font-bold leading-tight tracking-tight text-white',
            centered ? 'text-3xl md:text-4xl' : 'text-3xl md:text-4xl',
          )}
        >
          {title}
        </h1>
      ) : null}
      {subtitle ? (
        <p className={cn('mt-2 text-navy-200', centered ? 'mx-auto' : 'max-w-[56ch]')}>{subtitle}</p>
      ) : null}
    </header>
  )
}

export function PillFilterGroup({ options, value, onChange, className }) {
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {options.map((opt) => {
        const key = typeof opt === 'string' ? opt : opt.key
        const label = typeof opt === 'string' ? opt : opt.label
        const active = value === key
        return (
          <button
            key={key}
            type="button"
            onClick={() => onChange(key)}
            className={cn(
              'rounded-full border px-3 py-1.5 text-xs transition-colors',
              active
                ? 'border-gold-400/40 bg-gold-400/10 text-white'
                : 'border-white/10 bg-white/[0.03] text-navy-200 hover:border-white/20 hover:text-white',
            )}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}

export function KvRow({ label, value, className }) {
  return (
    <div
      className={cn(
        'flex items-center justify-between border-b border-dashed border-white/5 py-2 text-[13px] text-navy-200',
        className,
      )}
    >
      <span>{label}</span>
      <b className="text-white">{value}</b>
    </div>
  )
}

export function SideSectionTitle({ children, className }) {
  return (
    <h4
      className={cn(
        'mb-2.5 mt-5 px-2 text-[11px] font-semibold uppercase tracking-[0.15em] text-navy-300 first:mt-0',
        className,
      )}
    >
      {children}
    </h4>
  )
}

/**
 * ConsumerShell — 用户端页面标准外层壳
 *
 * 【角色定位】类似 AdminShell 的用户端版本。它统一了：
 *   1) 页面标题 + 描述 + 主 CTA
 *   2) 响应式内边距与最大宽度
 *   3) 动画进入效果
 *
 * 【使用示例】
 *   <ConsumerShell title="剧本创作" eyebrow="创作中心" subtitle="输入创意，几小时生成完整短剧">
 *     <YourContent />
 *   </ConsumerShell>
 *
 * 【设计令牌对齐】
 *   - 背景: inherit (由外层 consumer 布局负责)
 *   - 最大宽度: max-w-7xl
 *   - 内边距: py-10 sm:py-14
 *   - 动画: pageEnter from @/constants/motion
 */
const PAGE_MAX_WIDTH = {
  '4xl': 'max-w-4xl',
  '5xl': 'max-w-5xl',
  '6xl': 'max-w-6xl',
  '7xl': 'max-w-7xl',
  full: 'max-w-none',
}

/** C 端页面标准容器 — 居中 + 左右内边距 + 可选最大宽度 */
export function PageContainer({
  children,
  className,
  width = '7xl',
  as: Component = 'div',
  ...props
}) {
  return (
    <Component
      className={cn('sf-page-shell', PAGE_MAX_WIDTH[width] ?? PAGE_MAX_WIDTH['7xl'], className)}
      {...props}
    >
      {children}
    </Component>
  )
}

export function ConsumerShell({
  eyebrow,
  title,
  subtitle,
  action,
  children,
  className,
  containerClassName,
  align = 'left',
  fullWidth = false,
}) {
  const centered = align === 'center'

  return (
    <div className={cn('relative', containerClassName)}>
      {/* 标题区 */}
      <div
        className={cn(
          'sf-page-shell',
          fullWidth ? 'max-w-none' : 'max-w-7xl',
          'pt-10 sm:pt-14',
        )}
      >
        <div className={cn(centered ? 'mx-auto max-w-3xl text-center' : 'max-w-3xl', 'mb-10 sm:mb-12 animate-fade-in')}>
          {eyebrow && <SectionEyebrow>{eyebrow}</SectionEyebrow>}
          {title && (
            <h1 className="mt-3 text-3xl sm:text-4xl md:text-5xl font-bold leading-[1.1] tracking-tight text-white">
              {title}
            </h1>
          )}
          {subtitle && (
            <p className={cn('mt-4 text-base sm:text-lg text-navy-200', centered ? 'mx-auto max-w-2xl' : 'max-w-3xl')}>
              {subtitle}
            </p>
          )}
          {action && <div className={cn('mt-6 flex flex-wrap gap-3', centered && 'justify-center')}>{action}</div>}
        </div>

        {/* 内容区 */}
        {children && <div className={cn('animate-fade-in', className)}>{children}</div>}
      </div>
    </div>
  )
}

/** C 端列表页工具栏 — 搜索 + 排序/操作，避免 flex 挤压竖排 */
export function ConsumerListToolbar({ children, className }) {
  return <div className={cn('sf-toolbar', className)}>{children}</div>
}

export function ConsumerListToolbarSearch({
  value,
  onChange,
  placeholder = '搜索…',
  className,
  inputClassName,
}) {
  return (
    <div className={cn('sf-toolbar-search relative', className)}>
      <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-navy-400" />
      <input
        type="search"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={cn('sf-control h-11 w-full pl-10', inputClassName)}
      />
    </div>
  )
}

export function ConsumerListToolbarActions({ children, className }) {
  return <div className={cn('sf-toolbar-actions', className)}>{children}</div>
}
