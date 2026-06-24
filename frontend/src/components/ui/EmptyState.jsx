import { FileX, Search, Lock, WifiOff, PlusCircle, AlertTriangle } from 'lucide-react';
import Button from '@/components/ui/Button';
import { cn } from '@/utils/cn';
import { renderLucideIcon } from '@/utils/renderLucideIcon';

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
    description: '点击下方按钮创建第一个项目',
  },
  'error': {
    icon: AlertTriangle,
    title: '加载失败',
    description: '数据加载出错，请稍后重试',
  },
};

export default function EmptyState({
  type = 'no-data',
  title,
  description,
  action,
  actionLabel,
  onAction,
  secondaryAction,
  secondaryActionLabel,
  onSecondaryAction,
  icon,
  className,
  compact = false,
}) {
  const preset = presets[type] || presets['no-data'];
  const iconSizeClass = cn(compact ? 'w-8 h-8' : 'w-12 h-12', 'text-slate-500');
  
  const actionContent = action || (actionLabel && onAction ? (
    <Button variant="gold" size="sm" onClick={onAction}>
      {actionLabel}
    </Button>
  ) : null);

  const secondaryActionContent = secondaryAction || (secondaryActionLabel && onSecondaryAction ? (
    <Button variant="secondary" size="sm" onClick={onSecondaryAction}>
      {secondaryActionLabel}
    </Button>
  ) : null);

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center py-12 sm:py-16',
        compact ? 'py-8' : 'py-12 sm:py-16',
        className,
      )}
    >
      <div
        className={cn(
          'rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-5',
          compact ? 'w-14 h-14' : 'w-20 h-20',
        )}
      >
        {renderLucideIcon(icon || preset.icon, iconSizeClass)}
      </div>
      <h3 className={cn('font-semibold text-white mb-2', compact ? 'text-base' : 'text-lg')}>
        {title || preset.title}
      </h3>
      <p className={cn('text-slate-400 max-w-sm', compact ? 'text-xs' : 'text-sm')}>
        {description || preset.description}
      </p>
      {(actionContent || secondaryActionContent) && (
        <div className="mt-6 flex items-center gap-3 flex-wrap justify-center">
          {actionContent}
          {secondaryActionContent}
        </div>
      )}
    </div>
  );
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
      actionLabel={buttonText}
      onAction={onClick}
    />
  );
}
