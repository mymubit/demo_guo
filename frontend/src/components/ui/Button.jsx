import { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'

const variants = {
  primary:
    'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-premium hover:shadow-card-hover',
  gold:
    'bg-gradient-to-r from-gold-300 to-gold-500 text-navy-950 shadow-gold hover:from-gold-200 hover:to-gold-400',
  secondary:
    'border border-white/10 bg-slate-800/70 text-navy-100 hover:border-white/20 hover:bg-slate-700/70',
  ghost:
    'border border-white/5 bg-slate-900/40 text-navy-200 hover:border-white/20 hover:bg-white/[0.06] hover:text-white',
  danger:
    'border border-danger-500/35 bg-danger-500/12 text-danger-300 hover:bg-danger-500/20 hover:text-danger-100',
}

const sizes = {
  sm: 'h-9 px-3 text-xs',
  md: 'h-11 px-4 text-sm',
  lg: 'h-12 px-5 text-base',
}

const iconOnlySizes = {
  sm: 'h-9 w-9 p-0',
  md: 'h-10 w-10 p-0',
  lg: 'h-12 w-12 p-0',
}

const Button = forwardRef(function Button(
  {
    type = 'button',
    variant = 'secondary',
    size = 'md',
    isLoading = false,
    iconLeft,
    iconRight,
    iconOnly = false,
    disabled,
    className,
    children,
    ...props
  },
  ref,
) {
  const isDisabled = disabled || isLoading

  return (
    <button
      ref={ref}
      type={type}
      disabled={isDisabled}
      className={cn(
        'inline-flex shrink-0 items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 sf-focus-ring',
        'disabled:pointer-events-none disabled:opacity-55',
        iconOnly ? iconOnlySizes[size] : sizes[size],
        variants[variant] || variants.secondary,
        className,
      )}
      {...props}
    >
      {isLoading ? <Loader2 className={cn(ICON.md, 'animate-spin')} /> : iconLeft}
      {iconOnly ? <span className="sr-only">{children}</span> : children}
      {!isLoading && iconRight}
    </button>
  )
})

export default Button
