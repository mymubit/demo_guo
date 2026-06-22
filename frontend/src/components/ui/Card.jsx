import { motion } from 'framer-motion'
import { cn } from '@/utils/cn'
import { hoverLift } from '@/constants/motion'

const variants = {
  default: 'border border-gray-200 bg-white shadow-sm',
  glass: 'border border-gray-200 bg-white shadow-sm',
  gold: 'rounded-2xl border border-accent-300/50 bg-accent-50 shadow-sm',
  subtle: 'border border-gray-100 bg-gray-50',
  flat: 'border border-gray-200 bg-white',
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
        interactive && 'transition-shadow hover:shadow-md hover:border-gray-300',
        className,
      )}
      {...props}
    >
      {children}
    </Element>
  )
}
