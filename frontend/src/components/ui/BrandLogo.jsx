import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Film } from 'lucide-react'
import { BRAND_GRADIENT, BRAND_SHADOW } from '@/constants/brand'
import { ICON } from '@/constants/iconSizes'

const SIZE_MAP = {
  sm: { box: 'w-10 h-10 rounded-xl', icon: ICON.lg, film: 'text-navy-950' },
  md: { box: 'w-12 h-12 rounded-2xl', icon: ICON.xl, film: 'text-navy-950' },
  lg: { box: 'w-16 h-16 rounded-2xl', icon: 'w-8 h-8', film: 'text-navy-950' },
}

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

  const isAdmin = variant === 'admin'
  const titleColor = isAdmin ? 'text-white' : 'text-gold-400 group-hover:text-gold-300'
  const subtitleColor = 'text-slate-400'

  const box = (
    <motion.div
      whileHover={interactive ? { rotate: 10, scale: 1.08 } : undefined}
      className={`${s.box} flex items-center justify-center shrink-0`}
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
          <span className={`text-xl font-bold transition-colors ${titleColor}`}>
            ScriptForge
            {subtitle ? (
              <span className={`ml-1 text-sm font-normal ${subtitleColor}`}>{subtitle}</span>
            ) : (
              <span className={`ml-1 text-sm font-normal ${subtitleColor}`}>AI</span>
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
