export const motionTiming = {
  fast: { duration: 0.18, ease: 'easeOut' },
  base: { duration: 0.28, ease: 'easeOut' },
  slow: { duration: 0.36, ease: 'easeOut' },
}

export const pageEnter = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 8 },
  transition: motionTiming.slow,
}

export const cardEnter = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  transition: motionTiming.base,
}

export const listContainer = {
  animate: {
    transition: {
      staggerChildren: 0.04,
    },
  },
}

export const modalOverlay = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: motionTiming.fast,
}

export const modalPanel = {
  initial: { opacity: 0, scale: 0.96, y: 8 },
  animate: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.96, y: 8 },
  transition: motionTiming.base,
}

export const hoverLift = {
  y: -2,
  transition: motionTiming.fast,
}

export const pressTap = {
  scale: 0.99,
}
