import EChart from './EChart'
import { Card } from '@/components/ui'
import { cn } from '@/utils/cn'

/** 带 glass-card 标题的图表卡片 */
export default function AdminChartCard({
  title,
  subtitle,
  option,
  height = 280,
  minWidth = 0,
  className = '',
  loading = false,
  error,
  emptyText = '暂无数据',
}) {
  return (
    <Card className={cn('min-w-0', className)} padding="lg">
      {title ? <h3 className="text-lg font-semibold text-white mb-1.5">{title}</h3> : null}
      {subtitle ? <p className="text-sm text-navy-400 mb-5 leading-relaxed">{subtitle}</p> : null}
      <EChart
        option={option}
        height={height}
        minWidth={minWidth}
        loading={loading}
        error={error}
        emptyText={emptyText}
      />
    </Card>
  )
}
