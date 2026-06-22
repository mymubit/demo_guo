import { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const variants = {
  brand:
    'bg-gradient-to-r from-brand-500 to-brand-700 text-white shadow-premium hover:shadow-card-hover hover:-translate-y-0.5 transition-transform',
  accent:
    'bg-gradient-to-r from-accent-300 to-accent-500 text-slate-900 shadow-gold hover:from-accent-200 hover:to-accent-400',
  primary:
    'bg-gradient-to-r from-brand-500 to-brand-700 text-white shadow-premium hover:shadow-card-hover hover:-translate-y-0.5 transition-transform',
  gold:
    'bg-gradient-to-r from-accent-300 to-accent-500 text-slate-900 shadow-gold hover:from-accent-200 hover:to-accent-400',
  secondary:
    'border border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50',
  ghost:
    'border border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50 hover:text-gray-900',
  danger:
    'border border-danger/35 bg-danger-bg text-danger-300 hover:bg-danger/20 hover:text-danger-light',
  text: 'text-brand-400 hover:text-brand-300 underline-offset-2 hover:underline px-0 py-0 h-auto',
}

const sizes = {
  xs: 'h-7 px-2.5 text-xs',
  sm: 'h-9 px-3 text-xs',
  md: 'h-11 px-4 text-sm',
  lg: 'h-12 px-5 text-base',
}

const iconOnlySizes = {
  xs: 'h-7 w-7 p-0',
  sm: 'h-9 w-9 p-0',
  md: 'h-11 w-11 p-0',
  lg: 'h-12 w-12 p-0',
}

const Button = forwardRef(function Button(
  {
    type = 'button',
    variant = 'secondary',
    size = 'md',
    isLoading = false,
    icon,
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
  const leadingIcon = iconLeft ?? icon
  const sizeClass = iconOnly ? iconOnlySizes[size] || iconOnlySizes.md : sizes[size] || sizes.md
  const variantClass = variants[variant] || variants.secondary

  return (
    <button
      ref={ref}
      type={type}
      disabled={isDisabled}
      className={cn(
        'inline-flex shrink-0 items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/30 focus-visible:ring-offset-2 focus-visible:ring-offset-white',
        'disabled:pointer-events-none disabled:opacity-55',
        sizeClass,
        variantClass,
        className,
      )}
      {...props}
    >
      {isLoading ? <Loader2 className={cn(ICON.md, 'animate-spin')} /> : renderLucideIcon(leadingIcon)}
      {iconOnly ? <span className="sr-only">{children}</span> : children}
      {!isLoading && renderLucideIcon(iconRight)}
    </button>
  )
})

export default Button
