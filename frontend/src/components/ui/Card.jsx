import { motion } from 'framer-motion'
import { cn } from '@/utils/cn'
import { hoverLift } from '@/constants/motion'

const variants = {
  default: 'border border-navy-700/30 bg-navy-900/55 shadow-card backdrop-blur-xl',
  glass: 'glass-card shadow-card',
  gold: 'glass-card-gold shadow-gold',
  subtle: 'border border-navy-700/25 bg-navy-900/35',
  flat: 'border border-navy-800/70 bg-navy-950/30',
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

  return (
    <Element
      whileHover={interactive ? hoverLift : undefined}
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
