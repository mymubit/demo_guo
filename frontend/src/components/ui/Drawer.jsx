/**
 * Drawer 抽屉组件 — 右侧滑入的侧面板
 *
 * 设计令牌对齐:
 *  - 背景: sf-console-panel (深色主题)
 *  - 动画: 使用 motion.js 提供的 modalOverlay/抽屉
 *  - 尺寸: sm(320) / md(480) / lg(640) / xl(800)
 *  - 激活色: accent-400 (金色点缀)
 *
 * 用法:
 *   <Drawer open={open} onClose={() => setOpen(false)} title="编辑剧本">
 *     <YourContent />
 *   </Drawer>
 */

import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import Button from './Button'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'
import { modalOverlay } from '@/constants/motion'

const widths = {
  sm: 'w-80',
  md: 'w-[480px]',
  lg: 'w-[640px]',
  xl: 'w-[800px]',
}

export default function Drawer({
  open,
  title,
  description,
  width = 'md',
  footer,
  onClose,
  children,
  className,
  showClose = true,
}) {
  return (
    <AnimatePresence>
      {open ? (
        <>
          {/* 遮罩层 */}
          <motion.div
            {...modalOverlay}
            onClick={onClose}
            className="fixed inset-0 z-[90] bg-navy-950/70 backdrop-blur-sm"
          />
          {/* 抽屉 */}
          <motion.div
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300, duration: 0.25 }}
            className={cn(
              'fixed right-0 top-0 bottom-0 z-[95] flex flex-col border-l border-white/5 bg-navy-900/95 shadow-2xl',
              widths[width] || widths.md,
              className,
            )}
            role="dialog"
            aria-modal="true"
          >
            {/* 标题区 */}
            <div className="flex items-start justify-between gap-4 border-b border-white/5 px-6 py-5 shrink-0">
              <div className="min-w-0">
                {title && <h3 className="text-lg font-semibold text-white truncate">{title}</h3>}
                {description && (
                  <p className="mt-1 text-sm leading-relaxed text-navy-400">{description}</p>
                )}
              </div>
              {showClose && onClose && (
                <Button
                  variant="ghost"
                  size="sm"
                  iconOnly
                  iconLeft={<X className={ICON.md} />}
                  onClick={onClose}
                  className="rounded-lg shrink-0"
                >
                  关闭
                </Button>
              )}
            </div>

            {/* 内容区 */}
            <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>

            {/* 底部操作区 */}
            {footer && (
              <div className="border-t border-white/5 px-6 py-4 shrink-0 bg-navy-950/40">
                {footer}
              </div>
            )}
          </motion.div>
        </>
      ) : null}
    </AnimatePresence>
  )
}
