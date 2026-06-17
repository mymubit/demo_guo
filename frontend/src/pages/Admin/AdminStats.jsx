/**
 * 数据统计中心
 *
 * 包含：
 * - 顶部 KPI 卡片（4个）：今日项目数 / 成功率 / 平均耗时 / 今日总扣币
 * - 主体图表区（4个）：
 *   1. 调用量趋势（折线图）
 *   2. 技能使用排行 TOP10（横向条形图）
 *   3. 失败率 Top 5（柱状图）
 *   4. LLM Provider 用量分布（饼图）
 * - 底部：节点耗时分布表格
 *
 * 筛选：时间范围（7/30/90天）
 */
import { useEffect, useMemo, useState } from 'react'
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CalendarRange,
  CircleDollarSign,
  Clock3,
  Coins,
  Filter,
  Gauge,
  PieChart as PieChartIcon,
  RefreshCcw,
  TrendingUp,
  TriangleAlert,
} from 'lucide-react'

import AdminShell from '@/components/admin/AdminShell'
import { AdminPageHeader, AdminPanel } from '@/components/admin/AdminUI'
import { EChart } from '@/components/charts'
import { chartColors } from '@/components/charts/theme'
import { adminStats } from '@/services/api'
import { Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { cn } from '@/utils/cn'

const DAY_RANGES = [
  { value: 7, label: '近 7 天' },
  { value: 30, label: '近 30 天' },
  { value: 90, label: '近 90 天' },
]

const PROVIDER_PALETTE = [
  chartColors.gold,
  chartColors.goldLight,
  chartColors.purple,
  chartColors.blue,
  chartColors.green,
  chartColors.red,
  chartColors.cyan,
  chartColors.pink,
]

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '0'
  return Number(value).toLocaleString('zh-CN')
}

function formatDuration(ms) {
  if (!ms) return '0 s'
  if (ms < 1000) return `${ms} ms`
  const s = ms / 1000
  if (s < 60) return `${s.toFixed(1)} s`
  const m = s / 60
  return `${m.toFixed(1)} min`
}

function formatPercent(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return '0%'
  return `${Number(value).toFixed(digits)}%`
}

function KpiCard({ label, value, hint, icon: Icon, tone = 'default', trend }) {
  const tones = {
    default: 'text-navy-300 bg-slate-800/60 border-white/10',
    gold: 'text-gold-300 bg-gold-400/12 border-gold-400/25',
    success: 'text-success-300 bg-success-500/12 border-success-500/25',
    warning: 'text-warning-300 bg-warning-500/12 border-warning-500/25',
    danger: 'text-danger-300 bg-danger-500/12 border-danger-500/25',
  }
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs text-navy-400">{label}</div>
          <div className="mt-2 truncate text-3xl font-bold tracking-tight text-white">{value}</div>
          {hint ? <div className="mt-1 text-[11px] text-navy-400">{hint}</div> : null}
        </div>
        {Icon ? (
          <div className={cn('flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border', tones[tone] || tones.default)}>
            <Icon className={ICON.lg} />
          </div>
        ) : null}
      </div>
      {trend ? (
        <div
          className={cn(
            'mt-3 inline-flex items-center gap-1 text-xs',
            trend.up ? 'text-success-300' : 'text-danger-300',
          )}
        >
          {trend.up ? <ArrowUpRight className={ICON.sm} /> : <ArrowDownRight className={ICON.sm} />}
          <span>{trend.label}</span>
        </div>
      ) : null}
    </div>
  )
}

function FilterBar({ days, onChange, onRefresh, loading }) {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-slate-900/60 p-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex items-center gap-3">
        <Filter className={cn(ICON.md, 'text-navy-400')} />
        <span className="text-xs uppercase tracking-wider text-navy-400">时间范围</span>
        <div className="flex flex-wrap gap-1 rounded-full border border-white/10 bg-white/5 p-1 text-sm">
          {DAY_RANGES.map((r) => (
            <button
              key={r.value}
              type="button"
              onClick={() => onChange(r.value)}
              className={cn(
                'rounded-full px-4 py-1.5 font-medium transition-colors',
                days === r.value ? 'bg-white/10 text-white' : 'text-slate-300 hover:text-white',
              )}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={onRefresh}
        disabled={loading}
        className="inline-flex items-center gap-2"
      >
        <RefreshCcw className={cn(ICON.sm, loading && 'animate-spin')} />
        刷新
      </Button>
    </div>
  )
}

function buildTrendOption(rows) {
  const dates = rows.map((r) => r.date)
  const calls = rows.map((r) => r.calls || 0)
  const success = rows.map((r) => {
    const value = Number(r.success_rate || 0)
    return Math.round(value * 100) / 100
  })
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['调用量', '成功率(%)'], top: 0, right: 8 },
    grid: { left: 8, right: 16, top: 28, bottom: 4, containLabel: true },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: [
      { type: 'value', name: '调用量', position: 'left', axisLabel: { fontSize: 10 } },
      {
        type: 'value',
        name: '成功率(%)',
        position: 'right',
        min: 0,
        max: 100,
        splitLine: { show: false },
        axisLabel: { fontSize: 10, formatter: '{value}%' },
      },
    ],
    series: [
      {
        name: '调用量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: calls,
        itemStyle: { color: chartColors.gold },
        lineStyle: { width: 2, color: chartColors.gold },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(246,211,101,0.35)' },
              { offset: 1, color: 'rgba(246,211,101,0.02)' },
            ],
          },
        },
      },
      {
        name: '成功率(%)',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: success,
        itemStyle: { color: chartColors.green },
        lineStyle: { width: 2, color: chartColors.green },
      },
    ],
  }
}

function buildSkillRankingOption(rows) {
  if (!rows.length) return null
  const labels = rows.map((r) => r.skill_id)
  const data = rows.map((r) => ({
    value: r.calls,
    successRate: r.success_rate,
    itemStyle: {
      color: (r.success_rate || 0) >= 90 ? chartColors.gold : chartColors.purple,
      borderRadius: [0, 4, 4, 0],
    },
  }))
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params?.[0]
        if (!p) return ''
        const row = rows[p.dataIndex]
        return `<div style="font-size:12px">${p.name}<br/>调用量：${formatNumber(p.value)}<br/>成功率：${formatPercent(row?.success_rate)}</div>`
      },
    },
    grid: { left: 8, right: 36, top: 8, bottom: 8, containLabel: true },
    xAxis: { type: 'value', axisLabel: { fontSize: 10 } },
    yAxis: { type: 'category', data: labels, inverse: true, axisLabel: { fontSize: 10 } },
    series: [
      {
        type: 'bar',
        data,
        label: { show: true, position: 'right', fontSize: 10, color: '#cbd5e1' },
      },
    ],
  }
}

function buildFailureOption(rows) {
  if (!rows.length) return null
  const labels = rows.map((r) => r.skill_id)
  const data = rows.map((r) => ({
    value: r.failure_rate,
    itemStyle: {
      color: r.failure_rate >= 30 ? chartColors.red : r.failure_rate >= 10 ? chartColors.gold : chartColors.blue,
      borderRadius: [4, 4, 0, 0],
    },
  }))
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v) => `${v}%` },
    grid: { left: 8, right: 24, top: 8, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, rotate: 20 } },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%', fontSize: 10 } },
    series: [
      {
        type: 'bar',
        data,
        label: { show: true, position: 'top', fontSize: 10, color: '#cbd5e1', formatter: '{c}%' },
      },
    ],
  }
}

function buildProviderPieOption(items) {
  if (!items.length) return null
  const limited = items.slice(0, 8)
  return {
    tooltip: { trigger: 'item', valueFormatter: (v) => formatNumber(v) },
    legend: { orient: 'vertical', right: 4, top: 'middle', textStyle: { fontSize: 11, color: '#cbd5e1' } },
    series: [
      {
        type: 'pie',
        radius: ['40%', '68%'],
        center: ['38%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: '#0f172a', borderWidth: 2 },
        label: { show: false },
        data: limited.map((d, i) => ({
          name: `${d.provider}/${d.model}`,
          value: d.calls,
          itemStyle: { color: PROVIDER_PALETTE[i % PROVIDER_PALETTE.length] },
        })),
      },
    ],
  }
}

function NodeDurationTable({ rows }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="text-[11px] uppercase tracking-wider text-navy-400">
            <th className="px-3 py-2 text-left">Agent ID</th>
            <th className="px-3 py-2 text-right">样本数</th>
            <th className="px-3 py-2 text-right">平均</th>
            <th className="px-3 py-2 text-right">P50</th>
            <th className="px-3 py-2 text-right">P95</th>
            <th className="px-3 py-2 text-right">P99</th>
          </tr>
        </thead>
        <tbody>
          {!rows?.length ? (
            <tr>
              <td colSpan={6} className="px-3 py-6 text-center text-navy-400">暂无数据</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.agent_id} className="border-t border-white/5 hover:bg-indigo-500/[0.06]">
                <td className="px-3 py-2 text-slate-200 font-mono text-[12px]">{row.agent_id}</td>
                <td className="px-3 py-2 text-right tabular-nums text-slate-300">{formatNumber(row.run_count)}</td>
                <td className="px-3 py-2 text-right tabular-nums text-slate-200">{formatDuration(row.avg_ms)}</td>
                <td className="px-3 py-2 text-right tabular-nums text-slate-300">{formatDuration(row.p50)}</td>
                <td className="px-3 py-2 text-right tabular-nums text-slate-300">{formatDuration(row.p95)}</td>
                <td className="px-3 py-2 text-right tabular-nums text-slate-300">{formatDuration(row.p99)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

export default function AdminStats() {
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(false)
  const [kpi, setKpi] = useState(null)
  const [trend, setTrend] = useState([])
  const [skillRanking, setSkillRanking] = useState([])
  const [failureRanking, setFailureRanking] = useState([])
  const [providerUsage, setProviderUsage] = useState([])
  const [nodeDuration, setNodeDuration] = useState([])
  const [error, setError] = useState(null)

  const loadAll = async (nextDays = days) => {
    setLoading(true)
    setError(null)
    try {
      const [kpiRes, trendRes, skillRes, failRes, provRes, nodeRes] = await Promise.all([
        adminStats.kpi().catch(() => null),
        adminStats.trend({ days: nextDays }).catch(() => null),
        adminStats.skillRanking({ days: nextDays, limit: 10 }).catch(() => null),
        adminStats.failureRanking({ days: nextDays, limit: 5 }).catch(() => null),
        adminStats.llmProviderUsage({ days: nextDays }).catch(() => null),
        adminStats.nodeDuration({ days: nextDays }).catch(() => null),
      ])

      setKpi(kpiRes || null)
      setTrend((trendRes && trendRes.data) || [])
      setSkillRanking((skillRes && skillRes.items) || [])
      setFailureRanking((failRes && failRes.items) || [])
      setProviderUsage((provRes && provRes.items) || [])
      setNodeDuration((nodeRes && nodeRes.items) || [])
    } catch (err) {
      console.error(err)
      setError(err?.message || '数据加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll(days)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days])

  const trendOption = useMemo(() => buildTrendOption(trend || []), [trend])
  const skillOption = useMemo(() => buildSkillRankingOption(skillRanking), [skillRanking])
  const failureOption = useMemo(() => buildFailureOption(failureRanking), [failureRanking])
  const providerOption = useMemo(() => buildProviderPieOption(providerUsage), [providerUsage])

  return (
    <AdminShell>
      <div className="space-y-6">
        <AdminPageHeader
          title="数据统计中心"
          description="调用量 / 成功率 / 耗时 / 排行一览，用于评估 LLM 链路稳定性与节点健康度"
          actions={
            <Button
              variant="ghost"
              size="sm"
              onClick={() => loadAll(days)}
              disabled={loading}
              className="inline-flex items-center gap-2"
            >
              <RefreshCcw className={cn(ICON.sm, loading && 'animate-spin')} />
              刷新
            </Button>
          }
        />

        <FilterBar
          days={days}
          onChange={(v) => setDays(v)}
          onRefresh={() => loadAll(days)}
          loading={loading}
        />

        {error ? (
          <div className="rounded-2xl border border-danger-500/30 bg-danger-500/10 p-4 text-sm text-danger-200">
            {error}
          </div>
        ) : null}

        {/* KPI 卡片 */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            label="今日项目数"
            value={formatNumber(kpi?.today_projects)}
            icon={TrendingUp}
            tone="gold"
            hint="今日 0 点起创建的项目"
          />
          <KpiCard
            label="LLM 成功率（7 天）"
            value={formatPercent(kpi?.success_rate)}
            icon={Gauge}
            tone={(kpi?.success_rate || 0) >= 95 ? 'success' : 'warning'}
            hint="近 7 天 LLM 调用"
          />
          <KpiCard
            label="平均节点耗时"
            value={formatDuration(kpi?.avg_duration_ms)}
            icon={Clock3}
            tone="default"
            hint="近 7 天 completed 节点"
          />
          <KpiCard
            label="今日总扣币"
            value={formatNumber(kpi?.today_coins_spent)}
            icon={Coins}
            tone="warning"
            hint="消耗型流水（>0）"
          />
        </div>

        {/* 主体图表：2×2 */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <AdminPanel
            title="调用量趋势"
            sub="日级调用量 + 成功率"
            action={<CalendarRange className={cn(ICON.md, 'text-navy-400')} />}
          >
            {trendOption ? (
              <EChart option={trendOption} style={{ height: 280 }} />
            ) : (
              <div className="grid h-[280px] place-items-center text-navy-400 text-sm">暂无趋势数据</div>
            )}
          </AdminPanel>

          <AdminPanel
            title="技能使用排行 TOP 10"
            sub="按调用量降序"
            action={<BarChart3 className={cn(ICON.md, 'text-navy-400')} />}
          >
            {skillOption ? (
              <EChart option={skillOption} style={{ height: 280 }} />
            ) : (
              <div className="grid h-[280px] place-items-center text-navy-400 text-sm">暂无技能数据</div>
            )}
          </AdminPanel>

          <AdminPanel
            title="失败率 Top 5"
            sub="样本 ≥ 5 的失败率排序"
            action={<TriangleAlert className={cn(ICON.md, 'text-warning-300')} />}
          >
            {failureOption ? (
              <EChart option={failureOption} style={{ height: 280 }} />
            ) : (
              <div className="grid h-[280px] place-items-center text-navy-400 text-sm">暂无失败样本</div>
            )}
          </AdminPanel>

          <AdminPanel
            title="LLM Provider 用量分布"
            sub="按 provider/model 聚合"
            action={<PieChartIcon className={cn(ICON.md, 'text-navy-400')} />}
          >
            {providerOption ? (
              <EChart option={providerOption} style={{ height: 280 }} />
            ) : (
              <div className="grid h-[280px] place-items-center text-navy-400 text-sm">暂无 Provider 用量</div>
            )}
          </AdminPanel>
        </div>

        {/* 节点耗时分布 */}
        <AdminPanel
          title="创作节点耗时分布"
          sub="按 Agent 统计近 N 天 completed run 的耗时（毫秒）"
          action={<CircleDollarSign className={cn(ICON.md, 'text-navy-400')} />}
        >
          <NodeDurationTable rows={nodeDuration} />
        </AdminPanel>
      </div>
    </AdminShell>
  )
}
