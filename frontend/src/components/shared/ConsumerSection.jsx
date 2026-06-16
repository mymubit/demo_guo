/**
 * C 端章节标题与通用布局 primitive
 */
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
