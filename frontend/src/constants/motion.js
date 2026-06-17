// 统一动画规范 — 所有组件/页面统一使用此处定义的动效
// 设计原则:
// 1. 克制 — 仅在状态变化/内容出现时使用动效
// 2. 快速 — 基础动画不超过 300ms
// 3. 一致 — 全项目统一的 duration/easing
//
// 用法:
//   <motion.div {...motionTiming.fast} />
//   <motion.div {...motionLayout.panel} />

export const motionTiming = {
  instant: { transition: { duration: 0.08 } },
  fast: { transition: { duration: 0.15 } },
  base: { transition: { duration: 0.25 } },
  slow: { transition: { duration: 0.35 } },
  spring: { transition: { type: 'spring', stiffness: 400, damping: 30 } },
  springSoft: { transition: { type: 'spring', stiffness: 200, damping: 25 } },
}

// 入场动画
export const pageEnter = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  ...motionTiming.base,
}

// 容器级动画（用于包裹列表/网格）
export const containerFade = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  ...motionTiming.base,
}

// 列表交错入场
export const listStagger = {
  initial: {},
  animate: {
    transition: { staggerChildren: 0.05, delayChildren: 0.05 },
  },
}

export const listItemEnter = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  ...motionTiming.fast,
}

// 面板/卡片
export const cardFadeIn = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  ...motionTiming.base,
}

// 别名 — 与 cardFadeIn 相同，供 Card/Admin 页面统一引用
export const cardEnter = cardFadeIn

// 卡片悬浮效果 — 用于卡片 hover 微交互
export const hoverLift = {
  y: -2,
  scale: 1.02,
  transition: { duration: 0.15, ease: 'easeOut' },
}

export const cardHover = {
  whileHover: hoverLift,
  whileTap: { scale: 0.98 },
}

// 按钮点击反馈
export const buttonTap = {
  whileTap: { scale: 0.97 },
  ...motionTiming.instant,
}

// 模态框面板 — 带缩放+淡入
export const modalPanel = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
  ...motionTiming.base,
}

// 模态框遮罩
export const modalOverlay = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  ...motionTiming.fast,
}

// 抽屉面板 — 从右侧滑入
export const drawerPanel = {
  initial: { opacity: 0, x: 40 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 40 },
  ...motionTiming.base,
}

// 下拉菜单
export const dropdownPanel = {
  initial: { opacity: 0, y: -8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  ...motionTiming.fast,
}

// 进度条填充动画
export const progressFill = {
  initial: { scaleX: 0 },
  animate: { scaleX: 1 },
  ...motionTiming.slow,
}

// 图标旋转 — 用于加载状态
export const iconSpin = {
  animate: { rotate: 360 },
  transition: { repeat: Infinity, duration: 1, ease: 'linear' },
}

// 空状态图标微动画
export const emptyStateIcon = {
  initial: { scale: 0.8, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  ...motionTiming.springSoft,
}

// 节点脉冲 — 用于当前执行节点
export const nodePulse = {
  animate: {
    boxShadow: [
      '0 0 0 0 rgba(244, 183, 25, 0.4)',
      '0 0 0 10px rgba(244, 183, 25, 0)',
      '0 0 0 0 rgba(244, 183, 25, 0)',
    ],
  },
  transition: { repeat: Infinity, duration: 2 },
}

// 布局级动效组合 — 供页面/面板/列表统一 spread
export const motionLayout = {
  page: pageEnter,
  panel: cardFadeIn,
  card: cardEnter,
  list: listStagger,
  listItem: listItemEnter,
  modal: modalPanel,
  drawer: drawerPanel,
  dropdown: dropdownPanel,
}
