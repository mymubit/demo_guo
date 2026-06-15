import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Film } from 'lucide-react'
import { BRAND_GRADIENT, BRAND_SHADOW } from '@/constants/brand'
import { ICON } from '@/constants/iconSizes'

const SIZE_MAP = {
  sm: { box: 'w-10 h-10', icon: ICON.lg, film: 'text-white' },
  md: { box: 'w-12 h-12 rounded-2xl', icon: ICON.xl, film: 'text-navy-950' },
  lg: { box: 'w-16 h-16 rounded-2xl', icon: 'w-8 h-8', film: 'text-white' },
}

/**
 * @param {'consumer'|'admin'} variant — C 端金色 / 运营紫色
 */
export default function BrandLogo({
  variant = 'consumer',
  size = 'sm',
  showText = true,
  subtitle,
  to = '/',
  className = '',
  interactive = true,
}) {
  const s = SIZE_MAP[size] || SIZE_MAP.sm
  const gradient = BRAND_GRADIENT[variant] || BRAND_GRADIENT.consumer
  const shadow = BRAND_SHADOW[variant] || BRAND_SHADOW.consumer

  const box = (
    <motion.div
      whileHover={interactive ? { rotate: 10, scale: 1.08 } : undefined}
      className={`${s.box} rounded-xl flex items-center justify-center shrink-0`}
      style={{ background: gradient, boxShadow: shadow }}
    >
      <Film className={`${s.icon} ${s.film}`} />
    </motion.div>
  )

  const content = (
    <div className={`flex items-center gap-3 ${className}`}>
      {box}
      {showText && (
        <div className="min-w-0">
          <span className="text-xl font-bold">
            <span className="gradient-text">ScriptForge</span>
            {subtitle ? (
              <span className="text-white/70 ml-1 text-sm font-normal">{subtitle}</span>
            ) : (
              <span className="text-white/80 ml-1 text-sm font-normal">AI</span>
            )}
          </span>
        </div>
      )}
    </div>
  )

  if (to) {
    return (
      <Link to={to} className="group inline-flex">
        {content}
      </Link>
    )
  }
  return content
}
