import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '@/utils/cn'

type Variant = 'brand' | 'secondary' | 'ghost' | 'danger' | 'gold'
type Size = 'sm' | 'md' | 'lg'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
  size?: Size
  iconLeft?: ReactNode
  loading?: boolean
}

const variantClass: Record<Variant, string> = {
  brand: 'bg-brand-500 text-white hover:bg-brand-600 border-transparent',
  secondary: 'bg-white text-ink border-slate-200 hover:bg-slate-50',
  ghost: 'bg-transparent text-ink-muted border-transparent hover:bg-slate-100',
  danger: 'bg-red-600 text-white hover:bg-red-700 border-transparent',
  gold: 'bg-gold-400 text-navy-950 hover:bg-gold-300 border-transparent font-medium',
}

const sizeClass: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-9 px-4 text-sm',
  lg: 'h-11 px-5 text-sm',
}

export function Button({
  variant = 'brand',
  size = 'md',
  iconLeft,
  loading,
  className,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg border font-medium transition disabled:cursor-not-allowed disabled:opacity-50',
        variantClass[variant],
        sizeClass[size],
        className,
      )}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-r-transparent" />
      ) : (
        iconLeft
      )}
      {children}
    </button>
  )
}
