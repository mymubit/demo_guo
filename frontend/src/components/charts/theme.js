/** ScriptForge 管理后台深色主题（ECharts registerTheme） */
export const SCRIPTFORGE_CHART_THEME = 'scriptforge-dark'

export const chartColors = {
  gold: '#f4b719',
  goldLight: '#f7cb54',
  green: '#22c55e',
  emerald: '#10b981',
  cyan: '#22d3ee',
  blue: '#3b82f6',
  indigo: '#6366f1',
  purple: '#a855f7',
  red: '#ef4444',
  slate: '#64748b',
  text: '#cbd5e1',
  textMuted: '#64748b',
  axis: '#334155',
  grid: '#1e293b',
  background: 'transparent',
}

export const chartPalette = [
  chartColors.gold,
  chartColors.cyan,
  chartColors.emerald,
  chartColors.indigo,
  chartColors.blue,
  chartColors.purple,
  chartColors.red,
  '#f97316',
]

export const scriptforgeChartTheme = {
  color: chartPalette,
  backgroundColor: chartColors.background,
  textStyle: {
    color: chartColors.text,
    fontFamily:
      'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
  },
  title: {
    textStyle: { color: '#f1f5f9', fontSize: 16, fontWeight: 600 },
    subtextStyle: { color: chartColors.textMuted, fontSize: 12 },
  },
  legend: {
    top: 0,
    right: 0,
    itemWidth: 10,
    itemHeight: 10,
    textStyle: { color: chartColors.textMuted, fontSize: 11 },
    pageTextStyle: { color: chartColors.text },
  },
  tooltip: {
    backgroundColor: 'rgba(5, 20, 55, 0.96)',
    borderColor: 'rgba(141, 167, 211, 0.28)',
    extraCssText: 'box-shadow: 0 18px 48px -28px rgba(0, 0, 0, 0.75); border-radius: 12px;',
    textStyle: { color: '#e2e8f0', fontSize: 12 },
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: chartColors.axis } },
    axisTick: { lineStyle: { color: chartColors.axis } },
    axisLabel: { color: chartColors.textMuted, fontSize: 11 },
    splitLine: { lineStyle: { color: chartColors.grid, type: 'dashed' } },
  },
  valueAxis: {
    axisLine: { lineStyle: { color: chartColors.axis } },
    axisTick: { lineStyle: { color: chartColors.axis } },
    axisLabel: { color: chartColors.textMuted, fontSize: 11 },
    splitLine: { lineStyle: { color: chartColors.grid, type: 'dashed' } },
  },
  line: {
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { width: 2 },
  },
  bar: {
    itemStyle: { borderRadius: [6, 6, 0, 0] },
  },
  pie: {
    itemStyle: { borderColor: '#0f172a', borderWidth: 2 },
    label: { color: chartColors.text },
  },
  graph: {
    itemStyle: { borderColor: '#334155' },
    lineStyle: { color: '#475569', curveness: 0.2 },
    label: { color: chartColors.text },
  },
}
