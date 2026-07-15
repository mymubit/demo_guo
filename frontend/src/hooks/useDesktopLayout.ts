import { useEffect, useState } from 'react'

export const COMPACT_PC_MAX_WIDTH = 1399

export function isCompactPcWidth(width: number): boolean {
  return width <= COMPACT_PC_MAX_WIDTH
}

export function useCompactPcLayout(): boolean {
  const [isCompact, setIsCompact] = useState(() =>
    typeof window === 'undefined' ? false : isCompactPcWidth(window.innerWidth),
  )

  useEffect(() => {
    const media = window.matchMedia(`(max-width: ${COMPACT_PC_MAX_WIDTH}px)`)
    const handleChange = () => setIsCompact(media.matches)
    handleChange()
    media.addEventListener('change', handleChange)
    return () => media.removeEventListener('change', handleChange)
  }, [])

  return isCompact
}
