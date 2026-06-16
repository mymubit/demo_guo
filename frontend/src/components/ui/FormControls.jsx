import { forwardRef } from 'react'
import { cn } from '@/utils/cn'

function FieldShell({ label, hint, error, children, className }) {
  return (
    <label className={cn('block', className)}>
      {label ? <span className="sf-label">{label}</span> : null}
      {children}
      {error ? (
        <span className="mt-1.5 block text-xs text-danger-300">{error}</span>
      ) : hint ? (
        <span className="sf-help-text">{hint}</span>
      ) : null}
    </label>
  )
}

export const Input = forwardRef(function Input(
  { label, hint, error, className, inputClassName, leftIcon, rightAddon, ...props },
  ref,
) {
  return (
    <FieldShell label={label} hint={hint} error={error} className={className}>
      <div className="relative">
        {leftIcon ? (
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-navy-400">
            {leftIcon}
          </span>
        ) : null}
        <input
          ref={ref}
          className={cn('sf-control', leftIcon && 'pl-10', rightAddon && 'pr-16', error && 'border-danger-500/60', inputClassName)}
          {...props}
        />
        {rightAddon ? (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-navy-400">
            {rightAddon}
          </span>
        ) : null}
      </div>
    </FieldShell>
  )
})

export const Textarea = forwardRef(function Textarea(
  { label, hint, error, className, textareaClassName, rows = 4, ...props },
  ref,
) {
  return (
    <FieldShell label={label} hint={hint} error={error} className={className}>
      <textarea
        ref={ref}
        rows={rows}
        className={cn('sf-control resize-y leading-relaxed', error && 'border-danger-500/60', textareaClassName)}
        {...props}
      />
    </FieldShell>
  )
})

export const Select = forwardRef(function Select(
  { label, hint, error, className, selectClassName, children, ...props },
  ref,
) {
  return (
    <FieldShell label={label} hint={hint} error={error} className={className}>
      <select
        ref={ref}
        className={cn('sf-control appearance-none', error && 'border-danger-500/60', selectClassName)}
        {...props}
      >
        {children}
      </select>
    </FieldShell>
  )
})

export { FieldShell }
