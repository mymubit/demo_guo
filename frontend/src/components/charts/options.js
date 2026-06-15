import { chartColors, chartPalette } from './theme'

const tailwindColorMap = {
  'bg-gold-400/90': chartColors.gold,
  'bg-gold-400/80': chartColors.gold,
  'bg-gradient-to-t from-gold-600 to-gold-400': chartColors.gold,
  'bg-emerald-500/90': chartColors.emerald,
  'bg-cyan-500/90': chartColors.cyan,
  'bg-cyan-500/80': chartColors.cyan,
  'bg-purple-500/90': chartColors.purple,
  'bg-blue-500/80': chartColors.blue,
  'bg-green-500/85': chartColors.green,
  'bg-amber-500/80': chartColors.goldLight,
  'bg-red-500/80': chartColors.red,
  'bg-indigo-500/80': chartColors.indigo,
}

function resolveSeriesColor(color, index) {
  if (!color) return chartPalette[index % chartPalette.length]
  return tailwindColorMap[color] || chartPalette[index % chartPalette.length]
}

function shortDateLabel(label) {
  if (!label || typeof label !== 'string') return label
  return label.length >= 10 ? label.slice(5) : label
}

function topLegend() {
  return {
    top: 0,
    left: 0,
    right: 0,
    type: 'scroll',
    itemWidth: 10,
    itemHeight: 10,
    textStyle: { color: chartColors.textMuted, fontSize: 11 },
  }
}

/** 纵向柱状图（支持多系列） */
export function buildBarChartOption({ labels = [], series = [], stacked = false }) {
  if (!labels.length || !series.length) return null
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: series.length > 1 ? topLegend() : undefined,
    grid: { left: 12, right: 16, top: series.length > 1 ? 46 : 28, bottom: 12, containLabel: true },
    xAxis: {
      type: 'category',
      data: labels.map(shortDateLabel),
      axisLabel: { interval: 0, rotate: labels.length > 10 ? 35 : 0, fontSize: 11 },
    },
    yAxis: { type: 'value', splitNumber: 4 },
    series: series.map((s, idx) => ({
      name: s.name,
      type: 'bar',
      stack: stacked ? 'total' : undefined,
      barMaxWidth: 28,
      emphasis: { focus: 'series' },
      itemStyle: { color: resolveSeriesColor(s.color, idx), borderRadius: [6, 6, 0, 0] },
      data: s.values || [],
    })),
  }
}

/** 折线图（趋势） */
export function buildLineChartOption({ labels = [], series = [] }) {
  if (!labels.length || !series.length) return null
  return {
    tooltip: { trigger: 'axis' },
    legend: series.length > 1 ? topLegend() : undefined,
    grid: { left: 12, right: 16, top: series.length > 1 ? 46 : 28, bottom: 12, containLabel: true },
    xAxis: { type: 'category', data: labels.map(shortDateLabel), boundaryGap: false, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', splitNumber: 4 },
    series: series.map((s, idx) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: resolveSeriesColor(s.color, idx) },
      lineStyle: { width: 2 },
      data: s.values || [],
    })),
  }
}

/** 横向条形图推荐高度（按条数，避免单条撑满整卡） */
export function horizontalBarChartHeight(
  itemCount,
  { rowPx = 40, min = 100, max = 400, base = 56 } = {},
) {
  const n = Math.min(Math.max(Number(itemCount) || 0, 1), 12)
  return Math.min(max, Math.max(min, n * rowPx + base))
}

/** 横向条形图（排行） */
export function buildHorizontalBarOption({
  rows = [],
  valueKey = 'call_count',
  labelKey = 'display_name',
  valueSuffix = '',
  maxItems = 12,
  color = chartColors.gold,
  labelWidth = 120,
  labelMaxLen = 28,
}) {
  const list = [...rows]
    .sort((a, b) => (b[valueKey] || 0) - (a[valueKey] || 0))
    .slice(0, maxItems)
  if (!list.length) return null

  const labels = list.map((r) => {
    const main = r[labelKey] || r.action_key || r.display_name || '—'
    return main.length > labelMaxLen ? `${main.slice(0, labelMaxLen)}…` : main
  })
  const values = list.map((r) => r[valueKey] ?? 0)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params?.[0]
        if (!p) return ''
        const row = list[p.dataIndex]
        const full = row[labelKey] || row.action_key || row.display_name
        const val = p.value ?? 0
        const extra = row.coins_total != null ? ` · ${row.coins_total} 币` : ''
        const calls = row.call_count != null && valueKey !== 'call_count' ? ` · ${row.call_count} 次` : ''
        const tokenSplit =
          row.prompt_tokens != null || row.completion_tokens != null
            ? `<br/>输入 ${Number(row.prompt_tokens || 0).toLocaleString()} · 输出 ${Number(row.completion_tokens || 0).toLocaleString()}`
            : ''
        const costSplit =
          row.estimated_input_cost_yuan != null || row.estimated_output_cost_yuan != null
            ? `<br/>输入 ¥${Number(row.estimated_input_cost_yuan || 0).toFixed(4)} · 输出 ¥${Number(row.estimated_output_cost_yuan || 0).toFixed(4)}`
            : ''
        return `${full}<br/>${val.toLocaleString()}${valueSuffix}${tokenSplit}${costSplit}${extra}${calls}`
      },
    },
    grid: { left: 12, right: 28, top: 12, bottom: 12, containLabel: true },
    xAxis: { type: 'value', splitNumber: 4 },
    yAxis: {
      type: 'category',
      data: labels,
      inverse: true,
      axisLabel: { width: labelWidth, overflow: 'truncate' },
    },
    series: [
      {
        type: 'bar',
        data: values,
        barMaxWidth: 26,
        barCategoryGap: list.length <= 3 ? '55%' : '35%',
        itemStyle: {
          color,
          borderRadius: [0, 6, 6, 0],
        },
        label: {
          show: true,
          position: 'right',
          color: chartColors.textMuted,
          fontSize: 12,
          formatter: (p) => `${(p.value ?? 0).toLocaleString()}${valueSuffix}`,
        },
      },
    ],
  }
}

/** 环形/饼图 */
export function buildDonutChartOption({ items = [], nameKey = 'name', valueKey = 'value' }) {
  if (!items.length) return null
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      orient: 'vertical',
      right: 0,
      top: 'center',
      textStyle: { color: chartColors.textMuted, fontSize: 11 },
    },
    series: [
      {
        type: 'pie',
        radius: ['48%', '72%'],
        center: ['38%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: '#051437', borderWidth: 2 },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 12, fontWeight: 'bold' },
        },
        data: items.map((item, idx) => ({
          name: item[nameKey],
          value: item[valueKey] ?? 0,
          itemStyle: { color: chartPalette[idx % chartPalette.length] },
        })),
      },
    ],
    media: [
      {
        query: { maxWidth: 480 },
        option: {
          legend: {
            orient: 'horizontal',
            left: 'center',
            right: 'auto',
            bottom: 0,
            top: 'auto',
            type: 'scroll',
          },
          series: [{ center: ['50%', '42%'], radius: ['42%', '64%'] }],
        },
      },
    ],
  }
}

/** 执行 vs 跳过 占比 */
export function buildExecutedSkippedDonutOption({ executed = 0, skipped = 0 }) {
  const total = executed + skipped
  if (!total) return null
  return buildDonutChartOption({
    items: [
      { name: '执行', value: executed },
      { name: '跳过', value: skipped },
    ],
  })
}

/** Agent 执行量柱图 */
export function buildAgentVolumeOption({ groups = [] }) {
  if (!groups.length) return null
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 8, top: 16, bottom: 4, containLabel: true },
    xAxis: {
      type: 'category',
      data: groups.map((g) => g.agent_name || g.agent_id),
      axisLabel: { interval: 0, rotate: groups.length > 6 ? 25 : 0, fontSize: 10 },
    },
    yAxis: { type: 'value', splitNumber: 4 },
    series: [
      {
        type: 'bar',
        data: groups.map((g) => g.executedTotal ?? 0),
        itemStyle: { color: chartColors.gold, borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', color: chartColors.goldLight, fontSize: 10 },
      },
    ],
  }
}

/** 命中率横向条（0–100%） */
export function buildHitRateBarOption({ rows = [], labelKey = 'label', rateKey = 'rate' }) {
  if (!rows.length) return null
  const labels = rows.map((r) => r[labelKey])
  const values = rows.map((r) => Math.round((r[rateKey] || 0) * 100))
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params?.[0]
        return p ? `${p.name}: ${p.value}%` : ''
      },
    },
    grid: { left: 8, right: 32, top: 8, bottom: 8, containLabel: true },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    yAxis: { type: 'category', data: labels, inverse: true },
    series: [
      {
        type: 'bar',
        data: values.map((v) => ({
          value: v,
          itemStyle: {
            color: v >= 80 ? chartColors.green : v >= 50 ? chartColors.gold : chartColors.red,
            borderRadius: [0, 4, 4, 0],
          },
        })),
        label: { show: true, position: 'right', formatter: '{c}%', fontSize: 10 },
      },
    ],
  }
}
