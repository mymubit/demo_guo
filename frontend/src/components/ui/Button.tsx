import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '@/utils/cn'

type Variant = 'action' | 'secondary' | 'ghost' | 'danger' | 'shell'
type Size = 'sm' | 'md' | 'lg'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
  size?: Size
  iconLeft?: ReactNode
  loading?: boolean
}

const variantClass: Record<Variant, string> = {
  action: 'bg-action text-white hover:bg-action-hover border-transparent',
  secondary: 'bg-surface text-ink border-border hover:bg-canvas-muted',
  ghost: 'bg-transparent text-ink-muted border-transparent hover:bg-canvas-muted',
  danger: 'bg-danger text-white hover:opacity-90 border-transparent',
  shell: 'bg-shell-accent text-shell hover:bg-shell-accent-hover border-transparent font-medium',
}

const sizeClass: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-9 px-4 text-sm',
  lg: 'h-11 px-5 text-sm',
}

export function Button({
  variant = 'action',
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
