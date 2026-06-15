import { useEffect, useMemo, useState } from 'react'
import { Activity, AlertTriangle, BarChart3, Database, Gauge, ListFilter, Radar, RefreshCw } from 'lucide-react'

import AdminShell from '@/components/admin/AdminShell'
import { AdminLoading, AdminPagination, AdminTabBar, AdminTable } from '@/components/admin/AdminUI'
import { EChart } from '@/components/charts'
import { adminMonitoring } from '@/services/api'

const TABS = [
  { key: 'overview', label: '总览大盘', icon: Activity },
  { key: 'frontend', label: '前端异常', icon: AlertTriangle },
  { key: 'backend', label: '后端异常', icon: Radar },
  { key: 'api', label: '接口性能', icon: Gauge },
  { key: 'sql', label: '慢 SQL', icon: Database },
  { key: 'events', label: '埋点事件', icon: BarChart3 },
  { key: 'alerts', label: '告警配置', icon: ListFilter },
]

const DEFAULT_FILTERS = { days: 1, keyword: '', level: '', page: 1, page_size: 10 }

function formatTime(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function StatCard({ label, value, hint, tone = 'text-white' }) {
  return (
    <div className="rounded-2xl border border-navy-700/40 bg-navy-900/55 p-5">
      <p className="text-xs text-navy-400">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${tone}`}>{value ?? 0}</p>
      {hint ? <p className="mt-1 text-xs text-navy-500">{hint}</p> : null}
    </div>
  )
}

function FilterBar({ filters, onChange, onRefresh }) {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-navy-700/40 bg-navy-900/55 p-4 lg:flex-row lg:items-center">
      <select
        value={filters.days}
        onChange={(event) => onChange({ days: Number(event.target.value), page: 1 })}
        className="sf-control"
      >
        <option value={1}>最近 24 小时</option>
        <option value={7}>最近 7 天</option>
        <option value={30}>最近 30 天</option>
      </select>
      <input
        value={filters.keyword}
        onChange={(event) => onChange({ keyword: event.target.value, page: 1 })}
        placeholder="搜索 message / trace_id / hash"
        className="sf-control flex-1"
      />
      <select
        value={filters.level}
        onChange={(event) => onChange({ level: event.target.value, page: 1 })}
        className="sf-control"
      >
        <option value="">全部级别</option>
        <option value="info">INFO</option>
        <option value="warning">WARN</option>
        <option value="error">ERROR</option>
        <option value="critical">CRITICAL</option>
      </select>
      <button
        type="button"
        onClick={onRefresh}
        className="inline-flex items-center justify-center gap-2 rounded-xl border border-gold-500/30 px-4 py-2 text-sm font-semibold text-gold-300 hover:bg-gold-500/10"
      >
        <RefreshCw className="h-4 w-4" />
        刷新
      </button>
    </div>
  )
}

function buildTrendOption(rows = []) {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 20, top: 28, bottom: 32 },
    xAxis: { type: 'category', data: rows.map((item) => item.date) },
    yAxis: { type: 'value' },
    series: [
      {
        name: '异常数',
        type: 'line',
        smooth: true,
        areaStyle: {},
        data: rows.map((item) => item.count),
      },
    ],
  }
}

function buildTopApiOption(rows = []) {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 120, right: 24, top: 20, bottom: 24 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: rows.map((item) => item.path || 'unknown').reverse() },
    series: [{ type: 'bar', data: rows.map((item) => Math.round(item.avg_duration || 0)).reverse() }],
  }
}

function buildPieOption(rows = []) {
  return {
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        data: rows.map((item) => ({ name: item.event_type || 'unknown', value: item.count })),
      },
    ],
  }
}

function OverviewPanel({ data }) {
  const summary = data?.summary || {}
  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <StatCard label="前端异常" value={summary.frontend_errors} tone="text-red-300" />
        <StatCard label="后端异常" value={summary.backend_errors} tone="text-orange-300" />
        <StatCard label="接口请求" value={summary.api_requests} />
        <StatCard label="平均耗时" value={`${summary.api_avg_duration || 0} ms`} tone="text-gold-300" />
        <StatCard label="慢 SQL" value={summary.slow_sql} tone="text-purple-300" />
        <StatCard label="待处理告警" value={summary.open_alerts} tone="text-red-300" />
      </div>
      <div className="grid gap-4 xl:grid-cols-3">
        <div className="rounded-2xl border border-navy-700/40 bg-navy-900/55 p-4 xl:col-span-2">
          <p className="mb-3 text-sm font-semibold text-white">异常趋势</p>
          <EChart option={buildTrendOption(data?.error_trend)} height={260} />
        </div>
        <div className="rounded-2xl border border-navy-700/40 bg-navy-900/55 p-4">
          <p className="mb-3 text-sm font-semibold text-white">前端错误分布</p>
          <EChart option={buildPieOption(data?.frontend_error_distribution)} height={260} />
        </div>
      </div>
      <div className="rounded-2xl border border-navy-700/40 bg-navy-900/55 p-4">
        <p className="mb-3 text-sm font-semibold text-white">接口耗时排行</p>
        <EChart option={buildTopApiOption(data?.top_api_duration)} height={300} />
      </div>
    </div>
  )
}

function JsonPreview({ value }) {
  return <pre className="max-w-xl overflow-auto rounded-xl bg-navy-950/70 p-3 text-xs text-navy-200">{JSON.stringify(value || {}, null, 2)}</pre>
}

function ListPanel({ type, filters, onFilterChange }) {
  const [state, setState] = useState({ loading: true, items: [], pagination: null, error: '' })
  const params = useMemo(() => filters, [filters])

  useEffect(() => {
    let ignore = false
    async function load() {
      setState((prev) => ({ ...prev, loading: true, error: '' }))
      try {
        const loaders = {
          frontend: () => adminMonitoring.frontendEvents({ ...params, level: params.level }),
          backend: () => adminMonitoring.exceptions({ ...params, source: 'backend' }),
          api: () => adminMonitoring.apiPerformance(params),
          sql: () => adminMonitoring.slowSql(params),
          events: () => adminMonitoring.frontendEvents(params),
        }
        const result = await loaders[type]()
        if (!ignore) setState({ loading: false, items: result.items, pagination: result.pagination, error: '' })
      } catch (error) {
        if (!ignore) setState({ loading: false, items: [], pagination: null, error: error.message })
      }
    }
    load()
    return () => {
      ignore = true
    }
  }, [params, type])

  if (state.loading) return <AdminLoading label="监控数据加载中…" />
  if (state.error) return <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">{state.error}</div>

  const columnsByType = {
    frontend: [
      { key: 'event_type', title: '类型' },
      { key: 'level', title: '级别' },
      { key: 'route', title: '路由' },
      { key: 'message', title: '消息', render: (row) => <span className="line-clamp-2 max-w-sm">{row.message || row.name}</span> },
      { key: 'created_at', title: '时间', render: (row) => formatTime(row.created_at) },
    ],
    backend: [
      { key: 'exception_type', title: '异常' },
      { key: 'level', title: '级别' },
      { key: 'path', title: '路径', render: (row) => <span className="font-mono text-xs">{row.path}</span> },
      { key: 'message', title: '消息', render: (row) => <span className="line-clamp-2 max-w-sm">{row.message}</span> },
      { key: 'created_at', title: '时间', render: (row) => formatTime(row.created_at) },
    ],
    api: [
      { key: 'method', title: '方法' },
      { key: 'path', title: '路径', render: (row) => <span className="font-mono text-xs">{row.path}</span> },
      { key: 'status_code', title: '状态' },
      { key: 'duration_ms', title: '耗时', render: (row) => `${row.duration_ms} ms` },
      { key: 'created_at', title: '时间', render: (row) => formatTime(row.created_at) },
    ],
    sql: [
      { key: 'duration_ms', title: '耗时', render: (row) => `${row.duration_ms} ms` },
      { key: 'path', title: '路径', render: (row) => <span className="font-mono text-xs">{row.path}</span> },
      { key: 'sql_hash', title: 'Hash', render: (row) => <span className="font-mono text-xs">{row.sql_hash}</span> },
      { key: 'sql', title: 'SQL', render: (row) => <span className="line-clamp-2 max-w-lg">{row.sql}</span> },
      { key: 'created_at', title: '时间', render: (row) => formatTime(row.created_at) },
    ],
    events: [
      { key: 'event_type', title: '类型' },
      { key: 'name', title: '名称' },
      { key: 'route', title: '路由' },
      { key: 'payload', title: 'Payload', render: (row) => <JsonPreview value={row.payload} /> },
      { key: 'created_at', title: '时间', render: (row) => formatTime(row.created_at) },
    ],
  }

  return (
    <div className="space-y-4">
      <AdminTable columns={columnsByType[type]} rows={state.items} emptyText="暂无监控记录" />
      {state.pagination ? (
        <AdminPagination
          page={state.pagination.page}
          totalPages={state.pagination.total_pages}
          total={state.pagination.total}
          onPageChange={(page) => onFilterChange({ page })}
        />
      ) : null}
    </div>
  )
}

function AlertRulesPanel() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({
    name: '',
    metric_type: 'backend_error_count',
    comparator: 'gte',
    threshold: 10,
    window_minutes: 5,
    cooldown_minutes: 10,
    level: 'warning',
    path_pattern: '',
  })

  async function load() {
    setLoading(true)
    const result = await adminMonitoring.alertRules({ page_size: 50 })
    setRules(result.items)
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    await adminMonitoring.createAlertRule({ ...form, threshold: Number(form.threshold), window_minutes: Number(form.window_minutes) })
    setForm((prev) => ({ ...prev, name: '' }))
    load()
  }

  async function toggleRule(rule) {
    await adminMonitoring.updateAlertRule(rule.id, { is_enabled: !rule.is_enabled })
    load()
  }

  return (
    <div className="space-y-5">
      <form onSubmit={handleSubmit} className="grid gap-3 rounded-2xl border border-navy-700/40 bg-navy-900/55 p-4 lg:grid-cols-4">
        <input className="sf-control" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="规则名称" required />
        <select className="sf-control" value={form.metric_type} onChange={(e) => setForm({ ...form, metric_type: e.target.value })}>
          <option value="frontend_error_count">前端异常数</option>
          <option value="backend_error_count">后端异常数</option>
          <option value="api_avg_duration">接口平均耗时</option>
          <option value="api_error_rate">接口错误率</option>
          <option value="slow_sql_count">慢 SQL 数</option>
        </select>
        <input className="sf-control" type="number" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: e.target.value })} placeholder="阈值" />
        <button className="rounded-xl bg-gold-500 px-4 py-2 text-sm font-semibold text-navy-950 hover:bg-gold-400" type="submit">
          新增规则
        </button>
      </form>
      {loading ? (
        <AdminLoading label="告警规则加载中…" />
      ) : (
        <AdminTable
          rows={rules}
          emptyText="暂无告警规则"
          columns={[
            { key: 'name', title: '名称' },
            { key: 'metric_type', title: '指标' },
            { key: 'threshold', title: '阈值', render: (row) => `${row.comparator} ${row.threshold}` },
            { key: 'window_minutes', title: '窗口', render: (row) => `${row.window_minutes} 分钟` },
            { key: 'level', title: '级别' },
            {
              key: 'is_enabled',
              title: '状态',
              render: (row) => (
                <button type="button" onClick={() => toggleRule(row)} className="rounded-lg border border-navy-600 px-3 py-1 text-xs text-navy-100 hover:border-gold-500/40">
                  {row.is_enabled ? '已启用' : '已停用'}
                </button>
              ),
            },
          ]}
        />
      )}
    </div>
  )
}

export default function MonitoringDashboardPage() {
  const [active, setActive] = useState('overview')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [overview, setOverview] = useState({ loading: true, data: null, error: '' })
  const updateFilters = (patch) => setFilters((prev) => ({ ...prev, ...patch }))

  async function loadOverview() {
    setOverview((prev) => ({ ...prev, loading: true, error: '' }))
    try {
      const data = await adminMonitoring.overview({ days: filters.days })
      setOverview({ loading: false, data, error: '' })
    } catch (error) {
      setOverview({ loading: false, data: null, error: error.message })
    }
  }

  useEffect(() => {
    if (active === 'overview') loadOverview()
  }, [active, filters.days])

  return (
    <AdminShell title="业务监控" description="前端错误、接口性能、慢 SQL、埋点事件与告警配置统一查看。">
      <AdminTabBar tabs={TABS} active={active} onChange={setActive} stretch />
      <FilterBar filters={filters} onChange={updateFilters} onRefresh={active === 'overview' ? loadOverview : () => updateFilters({ page: 1 })} />
      {active === 'overview' ? (
        overview.loading ? <AdminLoading label="监控大盘加载中…" /> : <OverviewPanel data={overview.data} />
      ) : null}
      {['frontend', 'backend', 'api', 'sql', 'events'].includes(active) ? (
        <ListPanel type={active} filters={filters} onFilterChange={updateFilters} />
      ) : null}
      {active === 'alerts' ? <AlertRulesPanel /> : null}
    </AdminShell>
  )
}
