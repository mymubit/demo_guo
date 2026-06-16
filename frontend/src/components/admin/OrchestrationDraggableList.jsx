import { useState } from 'react'
import { GripVertical } from 'lucide-react'
import { cn } from '@/utils/cn'

/**
 * 通用拖拽排序列表（HTML5 DnD，无额外依赖）。
 */
export default function OrchestrationDraggableList({
  items = [],
  getId,
  onReorder,
  renderItem,
  disabled = false,
  className,
}) {
  const [dragId, setDragId] = useState(null)
  const [overId, setOverId] = useState(null)

  function handleDragStart(event, id) {
    if (disabled) return
    setDragId(id)
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', id)
  }

  function handleDragOver(event, id) {
    if (disabled || !dragId || dragId === id) return
    event.preventDefault()
    setOverId(id)
  }

  function handleDrop(event, targetId) {
    event.preventDefault()
    if (disabled || !dragId || dragId === targetId) {
      setDragId(null)
      setOverId(null)
      return
    }
    const ids = items.map(getId)
    const fromIdx = ids.indexOf(dragId)
    const toIdx = ids.indexOf(targetId)
    if (fromIdx < 0 || toIdx < 0) {
      setDragId(null)
      setOverId(null)
      return
    }
    const next = [...ids]
    next.splice(fromIdx, 1)
    next.splice(toIdx, 0, dragId)
    onReorder?.(next)
    setDragId(null)
    setOverId(null)
  }

  function handleDragEnd() {
    setDragId(null)
    setOverId(null)
  }

  return (
    <ul className={cn('space-y-1', className)}>
      {items.map((item, index) => {
        const id = getId(item)
        const isDragging = dragId === id
        const isOver = overId === id && dragId !== id
        return (
          <li
            key={id}
            draggable={!disabled}
            onDragStart={(e) => handleDragStart(e, id)}
            onDragOver={(e) => handleDragOver(e, id)}
            onDrop={(e) => handleDrop(e, id)}
            onDragEnd={handleDragEnd}
            className={cn(
              'flex items-stretch gap-1 rounded-xl border transition-colors',
              isDragging && 'opacity-50 border-gold-500/30',
              isOver && 'border-gold-500/50 bg-gold-500/5',
              !isDragging && !isOver && 'border-transparent',
            )}
          >
            <span
              className={cn(
                'flex items-center px-1.5 text-navy-500 shrink-0',
                disabled ? 'opacity-30 cursor-not-allowed' : 'cursor-grab active:cursor-grabbing',
              )}
              aria-hidden
            >
              <GripVertical className="w-3.5 h-3.5" />
            </span>
            <div className="flex-1 min-w-0">{renderItem(item, { index, isDragging, isOver })}</div>
          </li>
        )
      })}
    </ul>
  )
}
