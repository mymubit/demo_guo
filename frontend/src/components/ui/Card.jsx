import { motion } from 'framer-motion'
import { cn } from '@/utils/cn'
import { hoverLift } from '@/constants/motion'

const variants = {
  default: 'border border-white/5 bg-slate-900/60 shadow-card',
  glass: 'sf-console-panel shadow-card',
  gold: 'rounded-2xl border border-gold-400/30 bg-gold-400/5 shadow-gold',
  subtle: 'border border-white/5 bg-slate-900/40',
  flat: 'border border-white/5 bg-slate-950/50',
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
        'rounded-2xl',
        variants[variant] || variants.default,
        paddings[padding] || paddings.md,
        interactive && 'transition-shadow hover:shadow-card-hover',
        className,
      )}
      {...props}
    >
      {children}
    </Element>
  )
}
