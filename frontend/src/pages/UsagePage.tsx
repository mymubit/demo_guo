import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  DailyCostAlertBanner,
  useDailyCostAlert,
} from '@/components/DailyCostAlertBanner'
import { PageShell } from '@/components/layout/PageShell'
import { Input } from '@/components/ui/input'
import { formatApiError } from '@/services/errors'
import { listProjects } from '@/services/v3/projects'
import { getUsageSummary } from '@/services/v3/usage'
import type { UsageGroupBy, UsageMetrics, UsageSummaryRow } from '@/types/v3/domain'
import { isDailyCostOverAlert, parseEstimatedCost } from '@/utils/dailyCostAlert'
import { cn } from '@/utils/cn'
import { loadEcharts } from '@/utils/loadEcharts'

const PROJECTS_QUERY_KEY = ['v3', 'projects', 'list'] as const
const USAGE_QUERY_KEY = ['v3', 'usage', 'summary'] as const

const selectClassName =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50'

type UiGroupBy = Extract<UsageGroupBy, 'day' | 'model'>

function formatEstimatedCost(
  cost: string | null | undefined,
  unpricedCallCount?: number,
  callCount?: number,
): string {
  if (
    typeof unpricedCallCount === 'number' &&
    typeof callCount === 'number' &&
    callCount > 0 &&
    unpricedCallCount >= callCount
  ) {
    return '未定价'
  }
  if (cost == null || cost === '') return '未定价'
  return cost
}

function formatInt(value: number): string {
  return value.toLocaleString('zh-CN')
}

type ChartHostProps = {
  testId: string
  title: string
  option: Record<string, unknown> | null
}

type EchartsLike = {
  init: (el: HTMLElement) => {
    setOption: (opt: Record<string, unknown>) => void
    dispose: () => void
  }
}

function resolveEchartsModule(mod: unknown): EchartsLike {
  const candidate = mod as { init?: unknown; default?: { init?: unknown } }
  if (typeof candidate.init === 'function') {
    return candidate as EchartsLike
  }
  if (candidate.default && typeof candidate.default.init === 'function') {
    return candidate.default as EchartsLike
  }
  throw new Error('echarts 模块缺少 init')
}

function ChartHost({ testId, title, option }: ChartHostProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el || !option) return

    let disposed = false
    let chart: { setOption: (opt: Record<string, unknown>) => void; dispose: () => void } | null =
      null

    void loadEcharts()
      .then((mod) => {
        if (disposed || !containerRef.current) return
        const echarts = resolveEchartsModule(mod)
        chart = echarts.init(containerRef.current)
        if (disposed) {
          chart.dispose()
          chart = null
          return
        }
        chart.setOption(option)
      })
      .catch(() => {
        // 测试环境或加载失败时静默跳过图表渲染
      })

    return () => {
      disposed = true
      try {
        chart?.dispose()
      } catch {
        // jsdom 下 canvas dispose 可能抛错，忽略即可
      }
    }
  }, [option])

  return (
    <section className="sf-panel space-y-3 p-4">
      <h2 className="text-sm font-semibold text-ink">{title}</h2>
      <div
        ref={containerRef}
        data-testid={testId}
        className="h-64 w-full"
        role="img"
        aria-label={title}
      />
    </section>
  )
}

function buildTrendOption(rows: UsageSummaryRow[]): Record<string, unknown> | null {
  if (rows.length === 0) return null
  const categories = rows.map((row) => row.key)
  const tokens = rows.map((row) => row.total_tokens)
  const costs = rows.map((row) => {
    const cost = row.estimated_cost
    if (cost == null || cost === '') return null
    const n = Number(cost)
    return Number.isFinite(n) ? n : null
  })

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Token', '费用'] },
    grid: { left: 48, right: 48, top: 40, bottom: 32 },
    xAxis: { type: 'category', data: categories },
    yAxis: [
      { type: 'value', name: 'Token' },
      { type: 'value', name: '费用' },
    ],
    series: [
      { name: 'Token', type: 'line', data: tokens, smooth: true },
      { name: '费用', type: 'bar', yAxisIndex: 1, data: costs },
    ],
  }
}

function buildByModelOption(rows: UsageSummaryRow[]): Record<string, unknown> | null {
  if (rows.length === 0) return null
  const categories = rows.map((row) => row.label || row.key || '（空）')
  const tokens = rows.map((row) => row.total_tokens)
  const costs = rows.map((row) => {
    const cost = row.estimated_cost
    if (cost == null || cost === '') return null
    const n = Number(cost)
    return Number.isFinite(n) ? n : null
  })

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Token', '费用'] },
    grid: { left: 48, right: 48, top: 40, bottom: 32 },
    xAxis: { type: 'category', data: categories },
    yAxis: [
      { type: 'value', name: 'Token' },
      { type: 'value', name: '费用' },
    ],
    series: [
      { name: 'Token', type: 'bar', data: tokens },
      { name: '费用', type: 'bar', yAxisIndex: 1, data: costs },
    ],
  }
}

function MetricsCells({
  metrics,
  emphasize,
}: {
  metrics: UsageMetrics
  emphasize?: boolean
}) {
  const cellClass = emphasize ? 'px-3 py-2 font-medium text-ink' : 'px-3 py-2 text-ink'
  return (
    <>
      <td className={cellClass}>{formatInt(metrics.prompt_tokens)}</td>
      <td className={cellClass}>{formatInt(metrics.cached_prompt_tokens ?? 0)}</td>
      <td className={cellClass}>{formatInt(metrics.completion_tokens)}</td>
      <td className={cellClass}>{formatInt(metrics.total_tokens)}</td>
      <td className={cellClass}>{formatInt(metrics.call_count)}</td>
      <td className={cellClass}>
        {formatEstimatedCost(
          metrics.estimated_cost,
          metrics.unpriced_call_count,
          metrics.call_count,
        )}
      </td>
      <td className={cellClass}>{formatInt(metrics.unpriced_call_count)}</td>
    </>
  )
}

export function UsagePage() {
  const [projectId, setProjectId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [groupBy, setGroupBy] = useState<UiGroupBy>('day')

  const projectsQuery = useQuery({
    queryKey: PROJECTS_QUERY_KEY,
    queryFn: () => listProjects(),
  })

  const baseFilters = useMemo(
    () => ({
      project_id: projectId || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      live: 0 as const,
    }),
    [projectId, dateFrom, dateTo],
  )

  const tableQuery = useQuery({
    queryKey: [...USAGE_QUERY_KEY, { ...baseFilters, group_by: groupBy }],
    queryFn: () => getUsageSummary({ ...baseFilters, group_by: groupBy }),
  })

  const trendQuery = useQuery({
    queryKey: [...USAGE_QUERY_KEY, { ...baseFilters, group_by: 'day' as const }],
    queryFn: () => getUsageSummary({ ...baseFilters, group_by: 'day' }),
  })

  const byModelQuery = useQuery({
    queryKey: [...USAGE_QUERY_KEY, { ...baseFilters, group_by: 'model' as const }],
    queryFn: () => getUsageSummary({ ...baseFilters, group_by: 'model' }),
  })

  const tableRows = tableQuery.data?.rows ?? []
  const totals = tableQuery.data?.totals
  const trendOption = useMemo(
    () => buildTrendOption(trendQuery.data?.rows ?? []),
    [trendQuery.data?.rows],
  )
  const byModelOption = useMemo(
    () => buildByModelOption(byModelQuery.data?.rows ?? []),
    [byModelQuery.data?.rows],
  )

  const { today, threshold } = useDailyCostAlert()

  const isLoading = tableQuery.isLoading || projectsQuery.isLoading
  const loadError = tableQuery.isError
    ? formatApiError(tableQuery.error)
    : projectsQuery.isError
      ? formatApiError(projectsQuery.error)
      : null

  return (
    <PageShell title="用量" description="按项目与日期查看 Token 消耗与费用估算。">
      <div className="space-y-5">
        <DailyCostAlertBanner />
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block space-y-1.5 text-sm font-medium text-ink">
            项目
            <select
              className={selectClassName}
              value={projectId}
              onChange={(event) => setProjectId(event.target.value)}
              aria-label="项目"
            >
              <option value="">全部项目</option>
              {(projectsQuery.data ?? []).map((project) => (
                <option key={project.id} value={project.id}>
                  {project.title}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1.5 text-sm font-medium text-ink">
            开始日期
            <Input
              type="date"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
              aria-label="开始日期"
            />
          </label>
          <label className="block space-y-1.5 text-sm font-medium text-ink">
            结束日期
            <Input
              type="date"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
              aria-label="结束日期"
            />
          </label>
          <label className="block space-y-1.5 text-sm font-medium text-ink">
            分组
            <select
              className={selectClassName}
              value={groupBy}
              onChange={(event) => setGroupBy(event.target.value as UiGroupBy)}
              aria-label="分组"
            >
              <option value="day">按日</option>
              <option value="model">按模型</option>
            </select>
          </label>
        </section>

        {isLoading ? <p className="text-sm text-ink-muted">正在加载用量…</p> : null}
        {loadError ? <p className="text-sm text-danger">{loadError}</p> : null}

        {!tableQuery.isLoading && !tableQuery.isError ? (
          <section className="sf-panel space-y-3 overflow-x-auto p-4">
            <h2 className="text-sm font-semibold text-ink">汇总</h2>
            {tableRows.length === 0 && !totals ? (
              <p className="text-sm text-ink-muted">暂无用量数据。</p>
            ) : (
              <table className="w-full min-w-[40rem] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-ink-muted">
                    <th className="px-3 py-2 font-medium">分组键</th>
                    <th className="px-3 py-2 font-medium">输入 Token</th>
                    <th className="px-3 py-2 font-medium">缓存命中</th>
                    <th className="px-3 py-2 font-medium">输出 Token</th>
                    <th className="px-3 py-2 font-medium">合计 Token</th>
                    <th className="px-3 py-2 font-medium">调用次数</th>
                    <th className="px-3 py-2 font-medium">估算费用</th>
                    <th className="px-3 py-2 font-medium">未定价调用</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((row) => {
                    const rowOver =
                      groupBy === 'day' &&
                      row.key === today &&
                      isDailyCostOverAlert(parseEstimatedCost(row.estimated_cost), threshold)
                    return (
                      <tr
                        key={row.key}
                        data-over-alert={rowOver ? 'true' : undefined}
                        className={cn(
                          'border-b border-border/70',
                          rowOver && 'bg-amber-50',
                        )}
                      >
                        <td className="px-3 py-2 text-ink">
                          {groupBy === 'model'
                            ? row.label || row.key || '—'
                            : row.key || '—'}
                        </td>
                        <MetricsCells metrics={row} />
                      </tr>
                    )
                  })}
                  {totals ? (
                    <tr className="bg-muted/30">
                      <td className="px-3 py-2 font-medium text-ink">合计</td>
                      <MetricsCells metrics={totals} emphasize />
                    </tr>
                  ) : null}
                </tbody>
              </table>
            )}
          </section>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-2">
          <ChartHost testId="usage-chart-trend" title="按日趋势" option={trendOption} />
          <ChartHost testId="usage-chart-by-model" title="按模型对比" option={byModelOption} />
        </div>
      </div>
    </PageShell>
  )
}
