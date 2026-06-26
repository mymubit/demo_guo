import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import Button from './Button'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'
import { modalOverlay, modalPanel } from '@/constants/motion'

const widths = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  '2xl': 'max-w-5xl',
  '3xl': 'max-w-6xl',
  '4xl': 'max-w-7xl',
  full: 'w-[98vw] max-w-[1600px]',
}

export default function Modal({
  open,
  title,
  description,
  width,
  size,
  footer,
  onClose,
  children,
  className,
}) {
  const resolvedWidth = widths[size || width || 'md'] || widths.md
  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          {...modalOverlay}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-navy-950/92 p-2 sm:p-4 backdrop-blur-md"
        >
          <motion.div
            {...modalPanel}
            role="dialog"
            aria-modal="true"
            className={cn(
              'sf-console-panel w-full max-h-[min(94vh,960px)] flex flex-col shadow-modal',
              resolvedWidth,
              className,
            )}
          >
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-white/10 px-6 sm:px-8 py-5 sm:py-6">
              <div>
                {title ? <h3 className="text-lg font-semibold text-white">{title}</h3> : null}
                {description ? <p className="mt-1 text-sm leading-relaxed text-slate-400">{description}</p> : null}
              </div>
              {onClose ? (
                <Button
                  variant="ghost"
                  size="sm"
                  iconOnly
                  iconLeft={<X className={ICON.md} />}
                  onClick={onClose}
                  className="rounded-lg"
                >
                  关闭
                </Button>
              ) : null}
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-6 sm:px-8 py-5 sm:py-6">{children}</div>
            {footer ? <div className="shrink-0 border-t border-white/10 px-6 sm:px-8 py-4 sm:py-5">{footer}</div> : null}
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
