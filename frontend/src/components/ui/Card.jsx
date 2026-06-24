import { motion } from 'framer-motion'
import { cn } from '@/utils/cn'
import { hoverLift } from '@/constants/motion'

const variants = {
  default: 'border border-white/8 bg-white/[0.04] backdrop-blur-sm rounded-card shadow-card',
  glass: 'border border-white/10 bg-white/[0.06] backdrop-blur-md',
  elevated: 'border border-white/10 bg-slate-900/60 shadow-lg',
  gold: 'border border-gold-500/20 bg-gold-500/10',
  subtle: 'border border-white/5 bg-white/[0.02]',
  flat: 'border border-white/8 bg-white/[0.03]',
}

const paddings = {
  none: '',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
  xl: 'p-8',
}

export default function Card({
  as: Component = 'div',
  variant = 'default',
  padding = 'md',
  interactive = false,
  className,
  children,
  ...props
}) {
  const isMotion = interactive || Component === motion.div
  const Element = isMotion ? motion.div : Component
  const motionProps = interactive ? { whileHover: hoverLift } : {}

  return (
    <Element
      {...motionProps}
      className={cn(
        'rounded-xl',
        variants[variant] || variants.default,
        paddings[padding] || paddings.md,
        interactive && 'transition-all hover:border-gold-500/30 hover:bg-white/[0.08] hover:-translate-y-0.5 hover:shadow-card-hover',
        className,
      )}
      {...props}
    >
      {children}
    </Element>
  )
}
