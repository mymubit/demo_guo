import { getThemeMeta } from '@/constants/themeMeta'

const EMOJI_SIZE = {
  sm: 'text-lg',
  md: 'text-xl',
  lg: 'text-3xl',
  xl: 'text-4xl',
}

/**
 * 统一题材展示：emoji + 名称 + 主题色底
 */
export default function ThemeBadge({ themeKey, theme, size = 'sm', showName = true, active, className = '' }) {
  const meta = theme?.key ? theme : getThemeMeta(themeKey || theme)
  if (!meta?.name && !meta?.emoji) return null

  const emojiClass = EMOJI_SIZE[size] || EMOJI_SIZE.sm

  if (size === 'lg' || size === 'xl') {
    return (
      <div className={`text-center ${className}`}>
        <div className={`${emojiClass} mb-3`}>{meta.emoji}</div>
        {showName && <div className={`font-semibold mb-1 ${active ? 'text-white' : 'text-navy-100'}`}>{meta.name}</div>}
      </div>
    )
  }

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl ${className}`}
      style={{ background: `${meta.color}20` }}
    >
      <span className={emojiClass}>{meta.emoji}</span>
      {showName && (
        <span
          className={`font-medium ${size === 'md' ? 'text-sm' : 'text-xs'}`}
          style={{ color: meta.color }}
        >
          {meta.name}
        </span>
      )}
    </div>
  )
}
