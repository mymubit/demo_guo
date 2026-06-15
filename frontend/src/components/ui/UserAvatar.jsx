import { useState } from 'react'

export default function UserAvatar({
  src,
  name = '',
  phone = '',
  size = 'md',
  className = '',
}) {
  const [broken, setBroken] = useState(false)
  const initial = name?.charAt(0) || phone?.slice(-2) || 'U'

  const sizeClass =
    size === 'lg' ? 'w-28 h-28 text-4xl' : size === 'sm' ? 'w-8 h-8 text-sm' : 'w-16 h-16 text-xl'

  const showImg = src && !broken

  return (
    <div
      className={`rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center font-bold text-navy-950 overflow-hidden shrink-0 ${sizeClass} ${className}`}
    >
      {showImg ? (
        <img
          src={src}
          alt={name || 'avatar'}
          className="w-full h-full object-cover"
          onError={() => setBroken(true)}
        />
      ) : (
        initial
      )}
    </div>
  )
}
