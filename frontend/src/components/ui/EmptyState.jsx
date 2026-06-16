import { FileX, Search, Lock, WifiOff, PlusCircle } from 'lucide-react'
import Button from '@/components/ui/Button'
import { cn } from '@/utils/cn'

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
  icon,
  className,
  compact = false,
}) {
  const preset = presets[type] || presets['no-data']
  const Icon = icon || preset.icon

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
          'rounded-2xl bg-slate-800/60 flex items-center justify-center mb-4',
          compact ? 'w-12 h-12' : 'w-16 h-16',
        )}
      >
        <Icon className={cn(compact ? 'w-6 h-6' : 'w-8 h-8', 'text-slate-500')} />
      </div>
      <h3 className={cn('font-semibold text-white mb-1', compact ? 'text-sm' : 'text-base')}>
        {title || preset.title}
      </h3>
      <p className={cn('text-slate-400 mb-4', compact ? 'text-xs' : 'text-sm')}>
        {description || preset.description}
      </p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

// 便捷子组件 — 直接在页面调用
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
