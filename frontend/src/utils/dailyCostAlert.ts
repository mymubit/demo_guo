/** Asia/Shanghai 日历日 YYYY-MM-DD（与 usage summary 一致）。 */
export function getShanghaiDateString(date: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date)
}

export function parseEstimatedCost(cost: string | null | undefined): number | null {
  if (cost == null || cost === '') return null
  const n = Number(cost)
  return Number.isFinite(n) ? n : null
}

/** 阈值已配置且今日估算费用严格大于阈值时告警。 */
export function isDailyCostOverAlert(
  todayCost: number | null,
  threshold: number | null | undefined,
): boolean {
  if (threshold == null || !Number.isFinite(threshold)) return false
  if (todayCost == null) return false
  return todayCost > threshold
}
