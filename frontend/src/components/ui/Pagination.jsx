import { ChevronLeft, ChevronRight } from 'lucide-react'
import Button from './Button'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'

export default function Pagination({
  page,
  totalPages,
  total,
  onPageChange,
  className,
  compact = false,
}) {
  if (!totalPages || totalPages <= 1) return null

  return (
    <div className={cn('flex items-center justify-between gap-4 pt-2', className)}>
      <div className="text-sm text-navy-400">
        {compact ? `第 ${page} / ${totalPages} 页` : `共 ${total ?? 0} 条，第 ${page} / ${totalPages} 页`}
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          iconOnly
          iconLeft={<ChevronLeft className={ICON.md} />}
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          上一页
        </Button>
        <Button
          variant="secondary"
          size="sm"
          iconOnly
          iconLeft={<ChevronRight className={ICON.md} />}
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          下一页
        </Button>
      </div>
    </div>
  )
}
