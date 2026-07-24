import { useQuery } from '@tanstack/react-query'
import { getSystemConfig } from '@/services/v3/system'
import { getUsageSummary } from '@/services/v3/usage'
import {
  getShanghaiDateString,
  isDailyCostOverAlert,
  parseEstimatedCost,
} from '@/utils/dailyCostAlert'

const SYSTEM_CONFIG_QUERY_KEY = ['v3', 'system', 'config'] as const
const TODAY_USAGE_QUERY_KEY = ['v3', 'usage', 'summary', 'today'] as const

function formatCostYuan(value: number): string {
  return String(value)
}

export function useDailyCostAlert() {
  const today = getShanghaiDateString()

  const configQuery = useQuery({
    queryKey: SYSTEM_CONFIG_QUERY_KEY,
    queryFn: getSystemConfig,
  })

  const usageQuery = useQuery({
    queryKey: [...TODAY_USAGE_QUERY_KEY, today],
    queryFn: () =>
      getUsageSummary({
        group_by: 'day',
        date_from: today,
        date_to: today,
        live: 0,
      }),
  })

  const threshold = configQuery.data?.effective.daily_cost_alert_cny ?? null
  const todayRow = (usageQuery.data?.rows ?? []).find((row) => row.key === today)
  const todayCost =
    parseEstimatedCost(todayRow?.estimated_cost) ??
    parseEstimatedCost(usageQuery.data?.totals.estimated_cost)
  const isOver = isDailyCostOverAlert(todayCost, threshold)

  return {
    today,
    threshold,
    todayCost,
    isOver,
    isLoading: configQuery.isLoading || usageQuery.isLoading,
  }
}

export function DailyCostAlertBanner() {
  const { isOver, todayCost, threshold } = useDailyCostAlert()

  if (!isOver || todayCost == null || threshold == null) return null

  return (
    <p
      role="alert"
      data-testid="daily-cost-alert-banner"
      className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900"
    >
      今日估算费用 {formatCostYuan(todayCost)} 元已超过预警阈值 {formatCostYuan(threshold)}{' '}
      元。
    </p>
  )
}
