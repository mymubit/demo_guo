import { FileX, Search, Lock, WifiOff, PlusCircle } from 'lucide-react'
import Button from '@/components/ui/Button'
import { cn } from '@/utils/cn'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const presets = {
  'no-data': {
    icon: FileX,
    title: '暂无数据',
    description: '当前筛选条件下没有数据，请尝试调整筛选条件',
  },
  'no-result': {
    icon: Search,
    title: '未找到结果',
    description: '尝试调整搜索关键词或清空筛选条件',
  },
  'no-permission': {
    icon: Lock,
    title: '暂无权限',
    description: '请联系管理员开通访问权限',
  },
  'network-error': {
    icon: WifiOff,
    title: '网络异常',
    description: '请检查网络连接后重试',
  },
  'empty-create': {
    icon: PlusCircle,
    title: '还没有内容',
    description: '点击下方按钮创建第一项',
  },
}

export default function EmptyState({
  type = 'no-data',
  title,
  description,
  action,
  actionLabel,
  onAction,
  icon,
  className,
  compact = false,
}) {
  const preset = presets[type] || presets['no-data']
  const iconSizeClass = cn(compact ? 'w-6 h-6' : 'w-8 h-8', 'text-gray-400')
  const actionContent =
    action ||
    (actionLabel && onAction ? (
      <Button variant="brand" size="sm" onClick={onAction}>
        {actionLabel}
      </Button>
    ) : null)

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center',
        compact ? 'py-8' : 'py-16',
        className,
      )}
    >
      <div
        className={cn(
          'rounded-2xl bg-gray-100 flex items-center justify-center mb-4',
          compact ? 'w-12 h-12' : 'w-16 h-16',
        )}
      >
        {renderLucideIcon(icon || preset.icon, iconSizeClass)}
      </div>
      <h3 className={cn('font-semibold text-gray-900 mb-1', compact ? 'text-sm' : 'text-base')}>
        {title || preset.title}
      </h3>
      <p className={cn('text-gray-500 mb-4', compact ? 'text-xs' : 'text-sm')}>
        {description || preset.description}
      </p>
      {actionContent ? <div className="mt-2">{actionContent}</div> : null}
    </div>
  )
}

export function EmptyStateWithButton({
  type = 'no-data',
  title,
  description,
  buttonText = '新建',
  onClick,
  className,
}) {
  return (
    <EmptyState
      type={type}
      title={title}
      description={description}
      className={className}
      action={
        <Button variant="brand" size="sm" onClick={onClick}>
          {buttonText}
        </Button>
      }
    />
  )
}
