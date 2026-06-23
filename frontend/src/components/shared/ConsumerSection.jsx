/**
 * C 端章节标题与通用布局 primitive（浅色 dashboard 体系）
 */
import { Search } from 'lucide-react'
import { cn } from '@/utils/cn'

export function SectionEyebrow({ children, className }) {
  return (
    <span
      className={cn(
        'text-xs font-semibold uppercase tracking-[0.14em] text-brand-600 before:mr-2 before:inline-block before:h-px before:w-6 before:align-middle before:bg-brand-400',
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
            'mt-3 font-bold leading-tight tracking-tight text-gray-900',
            centered ? 'text-3xl md:text-4xl' : 'text-3xl md:text-4xl',
          )}
        >
          {title}
        </h1>
      ) : null}
      {subtitle ? (
        <p className={cn('mt-2 text-gray-500', centered ? 'mx-auto' : 'max-w-[56ch]')}>{subtitle}</p>
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
                ? 'border-brand-200 bg-brand-50 text-brand-700'
                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:text-gray-900',
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
        'flex items-center justify-between border-b border-dashed border-gray-200 py-2 text-[13px] text-gray-600',
        className,
      )}
    >
      <span>{label}</span>
      <b className="text-gray-900">{value}</b>
    </div>
  )
}

export function SideSectionTitle({ children, className }) {
  return (
    <h4
      className={cn(
        'mb-2.5 mt-5 px-2 text-[11px] font-semibold uppercase tracking-[0.15em] text-gray-400 first:mt-0',
        className,
      )}
    >
      {children}
    </h4>
  )
}

const PAGE_MAX_WIDTH = {
  '4xl': 'max-w-4xl',
  '5xl': 'max-w-5xl',
  '6xl': 'max-w-6xl',
  '7xl': 'max-w-7xl',
  full: 'max-w-none',
}

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
            <h1 className="mt-3 text-3xl sm:text-4xl md:text-5xl font-bold leading-[1.1] tracking-tight text-gray-900">
              {title}
            </h1>
          )}
          {subtitle && (
            <p className={cn('mt-4 text-base sm:text-lg text-gray-500', centered ? 'mx-auto max-w-2xl' : 'max-w-3xl')}>
              {subtitle}
            </p>
          )}
          {action && <div className={cn('mt-6 flex flex-wrap gap-3', centered && 'justify-center')}>{action}</div>}
        </div>

        {children && <div className={cn('animate-fade-in', className)}>{children}</div>}
      </div>
    </div>
  )
}

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
      <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
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
