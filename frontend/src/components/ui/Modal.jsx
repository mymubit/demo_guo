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
}

export default function Modal({
  open,
  title,
  description,
  width = 'md',
  footer,
  onClose,
  children,
  className,
}) {
  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          {...modalOverlay}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-navy-950/82 p-4 backdrop-blur-sm"
        >
          <motion.div
            {...modalPanel}
            role="dialog"
            aria-modal="true"
            className={cn('sf-console-panel w-full shadow-modal', widths[width] || widths.md, className)}
          >
            <div className="flex items-start justify-between gap-4 border-b border-white/5 px-6 py-5">
              <div>
                {title ? <h3 className="text-lg font-semibold text-white">{title}</h3> : null}
                {description ? <p className="mt-1 text-sm leading-relaxed text-navy-400">{description}</p> : null}
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
            <div className="px-6 py-5">{children}</div>
            {footer ? <div className="border-t border-white/5 px-6 py-4">{footer}</div> : null}
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
