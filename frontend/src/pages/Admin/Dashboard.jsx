import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Bot,
  FolderKanban,
  X,
  LayoutGrid,
  LayoutDashboard,
  Wallet,
  Coins,
  Cpu,
  AlertTriangle,
} from 'lucide-react'
import { admin } from '@/services/api'
import { resolveAgentId } from '@/utils/agentTerm'
import { formatLlmSourceLabel } from '@/utils/adminAgentLabels'
import ExecutionRunPanel from '@/components/shared/ExecutionRunPanel'
import DashboardOpsActionCards from '@/components/admin/DashboardOpsActionCards'
import { AdminPageHeader, AdminLoading, AdminMessage, AdminStatGrid, AdminTabBar } from '@/components/admin/AdminUI'
import { findAdminNavItem } from '@/config/adminNav'
import { Button, Card } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import {
  AdminChartCard,
  buildBarChartOption,
  buildDonutChartOption,
  buildHorizontalBarOption,
  horizontalBarChartHeight,
} from '@/components/charts'

function fmtYuan(v) {
  return `¥${Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
}

function fmtCostBreakdown({ input, output, total, digits = 4 } = {}) {
  const i = Number(input || 0)
  const o = Number(output || 0)
  const t = Number(total ?? i + o)
  const fmt = (n) => n.toFixed(digits)
  if (i > 0 || o > 0) {
    return `入 ¥${fmt(i)} / 出 ¥${fmt(o)} · 合计 ¥${fmt(t)}`
  }
  return fmtYuan(t)
}

function fmtTokenBreakdown({ prompt, completion, total, calls } = {}) {
  const p = Number(prompt || 0)
  const c = Number(completion || 0)
  const t = Number(total || p + c)
  const callHint = calls != null ? ` · ${calls} 次` : ''
  if (p > 0 || c > 0) {
    return `入 ${p.toLocaleString()} / 出 ${c.toLocaleString()} · 合计 ${t.toLocaleString()}${callHint}`
  }
  return `${t.toLocaleString()} Token${callHint}`
}

const DASHBOARD_TABS = [
  { key: 'overview', label: '今日总览', icon: LayoutDashboard },
  { key: 'commerce', label: '商业', icon: Wallet },
  { key: 'creation', label: '创作运营', icon: FolderKanban },
  { key: 'llm', label: '大模型成本', icon: Cpu },
]

function useDashboardCharts(dashboard) {
  const agentOps = dashboard?.agent_ops || {}
  const agentExecution = agentOps.execution || {}
  const agentRuns7d = agentExecution.runs_7d || []
  const agentStats = agentExecution.agent_stats || []
  const topFailedSubSkills = agentExecution.top_failed_sub_skills || []
  const topSubSkills = agentOps.top_sub_skills || []
  const llmUsage = dashboard?.llm_usage || {}
  const llmUsageTop = llmUsage.llm_usage_top || []
  const llmUsageBySource = llmUsage.llm_usage_by_source || []
  const skillTop = dashboard?.skill_usage_top || []

  const options = useMemo(() => {
    const userGrowth = dashboard?.user_growth_30d || []
    const memberShare = dashboard?.membership_share || []
    const finance7d = dashboard?.finance_7d || []
    const skillCalls7d = dashboard?.skill_calls_7d || []
    const creation7d = dashboard?.creation_7d || []
    const llmUsage7d = llmUsage.llm_usage_7d || []

    const bar = (labels, series, stacked = false) =>
      buildBarChartOption({ labels, series, stacked })

    const userGrowthSeries = [
      {
        key: 'new',
        name: '新增注册',
        color: 'bg-gradient-to-t from-gold-600 to-gold-400',
        labels: userGrowth.map((p) => p.date),
        values: userGrowth.map((p) => p.new_count || 0),
      },
    ]
    const financeSeries = [
      {
        key: 'recharge',
        name: '充值(元)',
        color: 'bg-emerald-500/90',
        labels: finance7d.map((d) => d.date),
        values: finance7d.map((d) => Number(d.recharge_yuan || 0)),
      },
      {
        key: 'membership',
        name: '会员(元)',
        color: 'bg-gold-400/90',
        labels: finance7d.map((d) => d.date),
        values: finance7d.map((d) => Number(d.membership_yuan || 0)),
      },
    ]
    const coinSeries = [
      {
        key: 'spent',
        name: '创作币消耗',
        color: 'bg-red-500/80',
        labels: finance7d.map((d) => d.date),
        values: finance7d.map((d) => d.coins_spent || 0),
      },
      {
        key: 'granted',
        name: '创作币发放',
        color: 'bg-blue-500/80',
        labels: finance7d.map((d) => d.date),
        values: finance7d.map((d) => d.coins_granted || 0),
      },
    ]
    const skillCallSeries = [
      {
        key: 'calls',
        name: '创作币扣费次数',
        color: 'bg-purple-500/90',
        labels: skillCalls7d.map((d) => d.date),
        values: skillCalls7d.map((d) => d.call_count || 0),
      },
    ]
    const llmCostSeries = [
      {
        key: 'input_cost',
        name: '输入费用(元)',
        color: 'bg-emerald-500/90',
        labels: llmUsage7d.map((d) => d.date),
        values: llmUsage7d.map((d) => Number(d.estimated_input_cost_yuan || 0)),
      },
      {
        key: 'output_cost',
        name: '输出费用(元)',
        color: 'bg-amber-500/80',
        labels: llmUsage7d.map((d) => d.date),
        values: llmUsage7d.map((d) => Number(d.estimated_output_cost_yuan || 0)),
      },
    ]
    const llmTokenSeries = [
      {
        key: 'prompt',
        name: '输入 Token',
        color: 'bg-cyan-500/90',
        labels: llmUsage7d.map((d) => d.date),
        values: llmUsage7d.map((d) => d.prompt_tokens || 0),
      },
      {
        key: 'completion',
        name: '输出 Token',
        color: 'bg-indigo-500/80',
        labels: llmUsage7d.map((d) => d.date),
        values: llmUsage7d.map((d) => d.completion_tokens || 0),
      },
    ]
    const creationSeries = [
      {
        key: 'creation',
        name: '新建项目',
        color: 'bg-cyan-500/80',
        labels: creation7d.map((d) => d.date),
        values: creation7d.map((d) => d.count || 0),
      },
    ]
    const agentRuns7dSeries = [
      {
        key: 'completed',
        name: '成功',
        color: 'bg-green-500/85',
        labels: agentRuns7d.map((d) => d.date),
        values: agentRuns7d.map((d) => d.completed_count || 0),
      },
      {
        key: 'failed',
        name: '失败',
        color: 'bg-red-500/80',
        labels: agentRuns7d.map((d) => d.date),
        values: agentRuns7d.map((d) => d.failed_count || 0),
      },
    ]

    return {
      userGrowth: bar(userGrowthSeries[0]?.labels, userGrowthSeries),
      skillCall: bar(skillCallSeries[0]?.labels, skillCallSeries),
      finance: bar(financeSeries[0]?.labels, financeSeries),
      coin: bar(coinSeries[0]?.labels, coinSeries),
      llmToken: bar(llmTokenSeries[0]?.labels, llmTokenSeries, true),
      llmCost: bar(llmCostSeries[0]?.labels, llmCostSeries, true),
      creation: bar(creationSeries[0]?.labels, creationSeries),
      agentRuns7d: bar(agentRuns7dSeries[0]?.labels, agentRuns7dSeries, true),
      memberShare: buildDonutChartOption({
        items: memberShare.map((item) => ({
          name: item.plan_name,
          value: item.member_count || 0,
        })),
      }),
      agentFailure: buildHorizontalBarOption({
        rows: agentStats.map((row) => ({
          display_name: resolveAgentId(row),
          failed_count: row.failed_count || 0,
        })),
        valueKey: 'failed_count',
        labelKey: 'display_name',
        valueSuffix: ' 次',
        color: '#f87171',
      }),
      failedSubSkill: buildHorizontalBarOption({
        rows: topFailedSubSkills.map((row) => ({
          display_name: `${row.agent_id || ''} · ${row.skill_id}`,
          failed_count: row.failed_count || 0,
        })),
        valueKey: 'failed_count',
        labelKey: 'display_name',
        valueSuffix: ' 次',
        color: '#fb7185',
      }),
      topSubSkills: buildHorizontalBarOption({
        rows: topSubSkills.map((row) => ({
          display_name: `${row.agent_name || row.agent_id} · ${row.skill_id}`,
          call_count: row.executed ?? 0,
        })),
        valueKey: 'call_count',
        labelKey: 'display_name',
        valueSuffix: ' 次',
        color: '#d4a853',
      }),
      skillTop: buildHorizontalBarOption({ rows: skillTop }),
      llmUsageTop: buildHorizontalBarOption({
        rows: llmUsageTop.map((row) => ({
          ...row,
          display_name: row.display_name || `${row.provider_name} / ${row.model_name}`,
        })),
        valueKey: 'total_tokens',
        valueSuffix: ' Token',
        labelKey: 'display_name',
      }),
      llmCostTop: buildHorizontalBarOption({
        rows: llmUsageTop,
        valueKey: 'estimated_cost_yuan',
        valueSuffix: ' 元',
        labelKey: 'display_name',
        color: '#10b981',
      }),
      llmBySource: buildHorizontalBarOption({
        rows: llmUsageBySource.map((row) => ({
          display_name: formatLlmSourceLabel(row.source_type, row.source_key),
          call_count: row.call_count,
        })),
        valueKey: 'call_count',
        labelKey: 'display_name',
        color: '#22d3ee',
        labelWidth: 200,
        labelMaxLen: 36,
      }),
    }
  }, [dashboard])

  return {
    options,
    agentOps,
    agentExecution,
    execToday: agentExecution.summary?.today || {},
    execPeriod: agentExecution.summary?.period || {},
    agentRuns7d,
    agentStats,
    topFailedSubSkills,
    topSubSkills,
    llmUsageTop,
    llmUsageBySource,
    skillTop,
  }
}

function CompareDelta({ today, yesterday, invert = false }) {
  const t = Number(today) || 0
  const y = Number(yesterday) || 0
  if (y === 0 && t === 0) {
    return <span className="text-[10px] text-navy-400">较昨日持平</span>
  }
  const diff = t - y
  let pct
  if (y === 0) {
    pct = t > 0 ? 100 : 0
  } else {
    pct = Math.round((diff / y) * 100)
  }
  const positive = invert ? diff < 0 : diff > 0
  const negative = invert ? diff > 0 : diff < 0
  const color = positive ? 'text-success-400' : negative ? 'text-danger-400' : 'text-navy-400'
  const arrow = diff > 0 ? '↑' : diff < 0 ? '↓' : '—'
  return (
    <span className={`text-[10px] ${color}`}>
      较昨日 {arrow}
      {Math.abs(pct)}%
    </span>
  )
}

function TodayFocusStrip({ summary, execToday, compare }) {
  const agentFailRate = execToday.run_count
    ? Math.round((execToday.failure_rate || 0) * 100)
    : null

  const cmp = compare || {}

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            label: '今日人民币收入',
            value: fmtYuan(summary.today_revenue),
            hint: `真实到账 · 会员 ${fmtYuan(summary.today_membership_yuan)} · 充值 ${fmtYuan(summary.today_recharge_yuan)}`,
            tone: 'text-success-400',
            delta: cmp.revenue_yuan,
          },
          {
            label: '今日新项目',
            value: summary.today_creations ?? 0,
            hint: `累计 ${summary.total_creations ?? 0} 个`,
            tone: 'text-cyan-400',
            delta: cmp.creations,
          },
          {
            label: '今日 Agent 执行',
            value: execToday.run_count ?? 0,
            hint:
              execToday.run_count > 0
                ? `失败 ${execToday.failed_count ?? 0} · ${agentFailRate}%`
                : '暂无执行',
            tone: (execToday.failed_count ?? 0) > 0 ? 'text-warning-400' : 'text-white',
            delta: cmp.agent_runs,
            deltaInvert: false,
          },
          {
            label: '今日 LLM 成本',
            value: fmtYuan(summary.today_llm_estimated_cost_yuan ?? 0),
            hint: `${fmtCostBreakdown({
              input: summary.today_llm_estimated_input_cost_yuan,
              output: summary.today_llm_estimated_output_cost_yuan,
              total: summary.today_llm_estimated_cost_yuan,
            })} · ${fmtTokenBreakdown({
              prompt: summary.today_llm_prompt_tokens,
              completion: summary.today_llm_completion_tokens,
              total: summary.today_llm_total_tokens,
              calls: summary.today_llm_call_count,
            }            )} · 粗算毛利 ${fmtYuan(summary.today_gross_yuan ?? 0)}`,
            tone: 'text-danger-400',
            delta: cmp.llm_cost_yuan,
            deltaInvert: true,
          },
        ].map((card) => (
          <Card
            key={card.label}
            padding="sm"
            className="border-gold-500/10 bg-gradient-to-br from-navy-900/80 to-navy-950/60"
          >
            <p className="text-xs text-navy-400">{card.label}</p>
            <p className={`text-2xl font-bold mt-1 ${card.tone}`}>{card.value}</p>
            <p className="text-[10px] text-navy-400 mt-1 leading-snug">{card.hint}</p>
            {card.delta ? (
              <div className="mt-1.5">
                <CompareDelta
                  today={card.delta.today}
                  yesterday={card.delta.yesterday}
                  invert={card.deltaInvert}
                />
              </div>
            ) : null}
          </Card>
        ))}
      </div>
    </div>
  )
}

function RunFilterBanner({ runFilterId, runLoading, runDetail, onClear }) {
  if (!runFilterId) return null
  return (
    <Card as="section" className="border-gold-500/30 bg-gold-400/5">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gold-400">Run 详情（从项目轨迹跳入）</h3>
          <p className="text-xs text-navy-300 font-mono mt-1">{runFilterId}</p>
        </div>
        <Button
          onClick={onClear}
          variant="ghost"
          size="sm"
          iconLeft={<X className={ICON.sm} />}
          className="rounded-lg text-xs"
        >
          关闭
        </Button>
      </div>
      {runLoading ? <p className="text-sm text-navy-400">加载执行记录…</p> : null}
      {!runLoading && !runDetail ? <p className="text-sm text-danger-300">未找到该执行记录</p> : null}
      {runDetail ? (
        <>
          <ExecutionRunPanel run={runDetail} />
          <Card variant="flat" padding="sm" className="mt-4">
            <p className="text-sm text-white mb-2">本次 Run 的 LLM 调用</p>
            <p className="text-xs text-navy-400 mb-3">
              {runDetail.llm_summary?.call_count ?? 0} 次 ·{' '}
              {fmtTokenBreakdown({
                prompt: runDetail.llm_summary?.prompt_tokens,
                completion: runDetail.llm_summary?.completion_tokens,
                total: runDetail.llm_summary?.total_tokens,
              })}{' '}
              ·{' '}
              {fmtCostBreakdown({
                input: runDetail.llm_summary?.estimated_input_cost_yuan,
                output: runDetail.llm_summary?.estimated_output_cost_yuan,
                total: runDetail.llm_summary?.estimated_cost_yuan,
              })}
            </p>
            {(runDetail.llm_usage || []).length ? (
              <ul className="space-y-2 text-xs max-h-[240px] overflow-y-auto">
                {runDetail.llm_usage.map((row) => (
                  <li
                    key={row.id}
                    className="flex flex-wrap justify-between gap-2 rounded-lg border border-white/5 bg-slate-900/40 px-3 py-2 text-navy-200"
                  >
                    <span>
                      {row.sub_skill_id || row.source_key || '—'} · {row.model_name}
                    </span>
                    <span className="text-navy-400">
                      入 {row.prompt_tokens ?? 0} / 出 {row.completion_tokens ?? 0} ·{' '}
                      {fmtCostBreakdown({
                        input: row.estimated_input_cost_yuan,
                        output: row.estimated_output_cost_yuan,
                        total: row.estimated_cost_yuan,
                      })}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-navy-400">该 Run 无 LLM 用量</p>
            )}
          </Card>
        </>
      ) : null}
    </Card>
  )
}

export default function Dashboard() {
  const dashNav = findAdminNavItem('/admin/dashboard')
  const [searchParams, setSearchParams] = useSearchParams()
  const runFilterId = (searchParams.get('run') || '').trim()
  const tab = searchParams.get('tab') || 'overview'

  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [runDetail, setRunDetail] = useState(null)
  const [runLoading, setRunLoading] = useState(false)
  const [llmRecalcBusy, setLlmRecalcBusy] = useState(false)
  const [failedProjects, setFailedProjects] = useState([])

  const reloadDashboard = () =>
    admin
      .getDashboard()
      .then(setDashboard)
      .catch((err) => setMessage({ type: 'error', text: err.message || '加载概览失败' }))

  useEffect(() => {
    reloadDashboard().finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    admin
      .listCreationProjects({ page: 1, page_size: 8, has_failed_run: 'true', facets: '0' })
      .then((res) => setFailedProjects(res.items || []))
      .catch(() => setFailedProjects([]))
  }, [dashboard?.date])

  useEffect(() => {
    if (!runFilterId) {
      setRunDetail(null)
      return undefined
    }
    let cancelled = false
    setRunLoading(true)
    admin
      .agentExecutionRun(runFilterId)
      .then((data) => {
        if (!cancelled) setRunDetail(data)
      })
      .catch(() => {
        if (!cancelled) setRunDetail(null)
      })
      .finally(() => {
        if (!cancelled) setRunLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [runFilterId])

  const summary = dashboard?.summary || {}
  const compare = dashboard?.compare || {}
  const commerceAlerts = dashboard?.commerce_alerts || {}
  const opsAlerts = dashboard?.ops_alerts || {}
  const charts = useDashboardCharts(dashboard)

  const setTab = (key) => {
    const next = new URLSearchParams(searchParams)
    next.set('tab', key)
    setSearchParams(next, { replace: true })
  }

  const clearRunFilter = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('run')
    setSearchParams(next, { replace: true })
  }

  async function handleRecalculateLlmCosts() {
    setLlmRecalcBusy(true)
    try {
      const res = await admin.recalculateLlmUsageCosts()
      setMessage({
        type: 'success',
        text: res?.message || `已重算 ${res?.recalculated ?? 0} 条历史用量`,
      })
      await reloadDashboard()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '重算失败' })
    } finally {
      setLlmRecalcBusy(false)
    }
  }

  if (loading) return <AdminLoading label="加载概览…" />

  const { options, agentOps, execToday, execPeriod, agentRuns7d, agentStats, topFailedSubSkills, topSubSkills, llmUsageTop, llmUsageBySource, skillTop } = charts

  return (
    <div className="space-y-6 w-full">
      <AdminMessage message={message} onClose={() => setMessage(null)} />
      <AdminPageHeader
        crumbs={[{ label: 'Console' }, { label: '今日总览' }]}
        title={`运营仪表盘 · ${dashboard?.date || new Date().toISOString().slice(0, 10)}`}
        subtitle={dashNav?.description}
      />

      <RunFilterBanner
        runFilterId={runFilterId}
        runLoading={runLoading}
        runDetail={runDetail}
        onClear={clearRunFilter}
      />

      <DashboardOpsActionCards opsAlerts={opsAlerts} failedProjects={failedProjects} />

      <AdminTabBar tabs={DASHBOARD_TABS} active={tab} onChange={setTab} stretch />

      {tab === 'overview' && (
        <div className="space-y-6">
          <TodayFocusStrip
            summary={summary}
            execToday={execToday}
            compare={compare}
          />
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <AdminChartCard
              title="近 30 天注册"
              subtitle="用户增长趋势"
              option={options.userGrowth}
              height={280}
              minWidth={420}
            />
            <AdminChartCard
              title="近 7 天新建项目"
              subtitle="创作活跃度"
              option={options.creation}
              height={280}
              minWidth={420}
            />
          </div>
          <p className="text-xs text-navy-400">
            人民币收入累计 {fmtYuan(summary.total_revenue)}（会员 {fmtYuan(summary.membership_revenue_total)} · 充值{' '}
            {fmtYuan(summary.recharge_revenue_total)}） · 30 天 LLM 真实成本{' '}
            {fmtYuan(summary.period_llm_estimated_cost_yuan ?? 0)} · 用户 {summary.total_users ?? 0} · 会员{' '}
            {summary.total_members ?? 0}
          </p>
        </div>
      )}

      {tab === 'commerce' && (
        <div className="space-y-6">
          <Card variant="subtle" padding="sm" className="space-y-2 text-sm text-navy-400">
            <p>
              <span className="text-success-300/90 font-medium">人民币收入</span>：充值、会员订单的真实到账金额（元）。
              <span className="text-cyan-300/90 font-medium ml-2">创作币</span>：站内经济系统，用户消耗/获得的是虚拟币，不等于人民币成本或收入。
            </p>
            <p>
              大模型 Token 真实 API 成本见
              <Link to="/admin/dashboard?tab=llm" className="text-gold-400 hover:underline mx-1">
                大模型成本
              </Link>
              Tab，勿与创作币扣费混淆。
            </p>
            <p className="text-xs text-navy-400">
              配置：
              <Link to="/admin/commerce/settings" className="text-gold-400 hover:underline mx-1">
                商业·钱包
              </Link>
              · Agent 配置见
              <Link to="/admin/agent" className="text-gold-400 hover:underline mx-1">
                Agent 中心
              </Link>
              <span className="inline-flex flex-wrap gap-3 ml-0 sm:ml-2 mt-2 sm:mt-0">
                <Link to="/admin/orders" className="text-gold-400/90 hover:text-gold-300">
                  订单
                </Link>
                <Link to="/admin/members/plans" className="text-gold-400/90 hover:text-gold-300">
                  会员与卡密
                </Link>
                {(commerceAlerts.pending_orders ?? 0) > 0 ? (
                  <Link
                    to="/admin/orders?status=pending"
                    className="text-warning-400 hover:text-warning-300 inline-flex items-center gap-1"
                  >
                    <AlertTriangle className={ICON.sm} />
                    待支付 {commerceAlerts.pending_orders}
                  </Link>
                ) : null}
              </span>
            </p>
          </Card>
          <div>
            <h3 className="text-sm font-medium text-success-300/90 mb-3 flex items-center gap-2">
              <Wallet className={ICON.md} />
              人民币收入（真实到账）
            </h3>
            <AdminStatGrid
              items={[
                { label: '累计人民币收入', value: fmtYuan(summary.total_revenue), hint: `今日 ${fmtYuan(summary.today_revenue)}` },
                { label: '会员收入', value: fmtYuan(summary.membership_revenue_total), hint: `今日 ${fmtYuan(summary.today_membership_yuan)}` },
                { label: '充值收入', value: fmtYuan(summary.recharge_revenue_total), hint: `今日 ${fmtYuan(summary.today_recharge_yuan)}` },
                { label: '总用户', value: summary.total_users ?? 0, hint: `今日 +${summary.today_new_users ?? 0}` },
                { label: '有效会员', value: summary.total_members ?? 0 },
              ]}
            />
          </div>
          <AdminChartCard title="近 7 天人民币收入（元）" option={options.finance} height={280} minWidth={460} />
          <div>
            <h3 className="text-sm font-medium text-cyan-300/90 mb-3 flex items-center gap-2">
              <Coins className={ICON.md} />
              创作币经济（站内虚拟币）
            </h3>
            <AdminStatGrid
              items={[
                { label: '全站钱包余额', value: summary.total_wallet_balance ?? 0, hint: '用户持有创作币合计' },
                { label: '累计发放创作币', value: summary.total_coins_recharged ?? 0, hint: `今日 +${summary.today_coins_recharged ?? 0}` },
                { label: '累计消耗创作币', value: summary.total_coins_spent ?? 0, hint: `今日 ${summary.today_coins_spent ?? 0}` },
              ]}
            />
          </div>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <AdminChartCard title="近 7 天创作币流动" subtitle="站内经济，非人民币" option={options.coin} height={280} minWidth={460} />
            <AdminChartCard title="会员套餐分布" option={options.memberShare} height={280} />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AdminChartCard
                title="近 30 天创作币扣费 Top"
                subtitle="主链/动作扣费，单位：创作币"
                option={options.skillTop}
                height={horizontalBarChartHeight(Math.min(skillTop.length, 10))}
                minWidth={520}
              />
            </div>
            <AdminChartCard
              title="近 7 天创作币扣费次数"
              subtitle="站内扣费笔数"
              option={options.skillCall}
              height={260}
              minWidth={420}
            />
          </div>
        </div>
      )}

      {tab === 'creation' && (
        <div className="space-y-6">
          <Card padding="md">
            <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
              <div>
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Bot className={`${ICON.md} text-gold-400`} />
                  创作与 Agent
                </h3>
                <p className="text-xs text-navy-400 mt-1">
                  drama_skills · 单项目轨迹见创作项目 · Drama 角色轨 SSOT
                </p>
              </div>
              <div className="flex flex-wrap gap-3 text-sm">
                <Link to="/admin/creation/projects" className="text-gold-400 hover:text-gold-300 inline-flex items-center gap-1">
                  <LayoutGrid className={ICON.md} />
                  创作项目
                </Link>
                <Link to="/admin/drama-models" className="text-gold-400 hover:text-gold-300">
                  Drama 模型
                </Link>
                <Link to="/admin/agent?tab=definitions" className="text-gold-400 hover:text-gold-300">
                  运行记录
                </Link>
              </div>
            </div>
            <AdminStatGrid
              items={[
                { label: '创作项目累计', value: summary.total_creations ?? 0, hint: `今日 +${summary.today_creations ?? 0}` },
                { label: '工作台项目', value: agentOps.workspace_projects ?? agentOps.workspace_project_count ?? 0, hint: `执行中 ${agentOps.drama_running_projects ?? 0}` },
                { label: '今日角色执行', value: execToday.run_count ?? 0, hint: `失败 ${execToday.failed_count ?? 0}` },
                {
                  label: '30 天失败率',
                  value: execPeriod.run_count ? `${Math.round((execPeriod.failure_rate || 0) * 100)}%` : '—',
                  hint: `${execPeriod.run_count ?? 0} 次`,
                },
                { label: '轨迹覆盖项目', value: agentOps.trace_project_count ?? 0 },
              ]}
            />
          </Card>

          <Card padding="md" className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Drama 角色执行监察</h3>
              <p className="text-xs text-navy-400 mt-1 leading-relaxed max-w-xl">
                按 drama.* 角色统计执行量与失败率；各角色 Token 与模型配置见 Drama 模型面板。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                to="/admin/drama-models"
                className="px-4 py-2 rounded-xl text-sm text-gold-300 border border-gold-500/30 bg-gold-500/10 hover:bg-gold-500/15 sf-focus-ring"
              >
                Drama 模型 & Token
              </Link>
              <Link
                to="/admin/creation/projects?failed_run=1"
                className="sf-focus-ring rounded-xl border border-white/10 px-4 py-2 text-sm text-navy-200 hover:bg-white/[0.06]"
              >
                有失败 run 的项目
              </Link>
            </div>
          </Card>
        </div>
      )}

      {tab === 'llm' && (
        <div className="space-y-6">
          <Card variant="flat" padding="sm" className="border-danger-500/15 bg-danger-500/5 text-sm text-navy-300">
            本 Tab 仅统计<strong className="text-danger-300/90 mx-1">大模型 API 真实成本</strong>（人民币，按 Token 单价估算）。
            与<strong className="text-cyan-300/90 mx-1">创作币扣费</strong>（站内经济）及
            <strong className="text-success-300/90 mx-1">充值/会员收入</strong>（真实到账）分开核算。
          </Card>
          {(summary.period_llm_total_tokens ?? 0) > 0 &&
          Number(summary.period_llm_estimated_cost_yuan ?? 0) <= 0 ? (
            <Card variant="flat" padding="sm" className="border-warning-500/20 bg-warning-500/5 text-sm text-warning-300/90">
              Token 用量已记录，但历史行的成本仍为 ¥0（调用写入时单价未命中）。请确认
              <Link to="/admin/model" className="text-gold-400 hover:underline mx-1">
                大模型
              </Link>
              各模板已保存单价且 Provider 从模板接入；然后
              <button
                type="button"
                disabled={llmRecalcBusy}
                onClick={handleRecalculateLlmCosts}
                className="text-gold-400 hover:text-gold-300 underline mx-1 disabled:opacity-50"
              >
                {llmRecalcBusy ? '重算中…' : '重算历史成本'}
              </button>
              或任意模型再点一次「保存单价」。
            </Card>
          ) : null}
          <AdminStatGrid
            columns={4}
            items={[
              {
                label: '今日 LLM 成本',
                value: fmtYuan(summary.today_llm_estimated_cost_yuan ?? 0),
                hint: `${fmtCostBreakdown({
                  input: summary.today_llm_estimated_input_cost_yuan,
                  output: summary.today_llm_estimated_output_cost_yuan,
                  total: summary.today_llm_estimated_cost_yuan,
                })} · ${fmtTokenBreakdown({
                  prompt: summary.today_llm_prompt_tokens,
                  completion: summary.today_llm_completion_tokens,
                  total: summary.today_llm_total_tokens,
                  calls: summary.today_llm_call_count,
                })}`,
              },
              {
                label: '30 天 LLM 成本',
                value: fmtYuan(summary.period_llm_estimated_cost_yuan ?? 0),
                hint: `${fmtCostBreakdown({
                  input: summary.period_llm_estimated_input_cost_yuan,
                  output: summary.period_llm_estimated_output_cost_yuan,
                  total: summary.period_llm_estimated_cost_yuan,
                })} · ${fmtTokenBreakdown({
                  prompt: summary.period_llm_prompt_tokens,
                  completion: summary.period_llm_completion_tokens,
                  total: summary.period_llm_total_tokens,
                  calls: summary.period_llm_call_count,
                })}`,
              },
              {
                label: '今日粗算毛利',
                value: fmtYuan(summary.today_gross_yuan ?? 0),
                hint: `人民币收入 ${fmtYuan(summary.today_revenue)} − LLM 成本`,
              },
              {
                label: '30 天粗算毛利',
                value: fmtYuan(summary.period_gross_yuan ?? 0),
                hint: `30 天人民币收入 ${fmtYuan(summary.period_revenue_yuan)} − LLM 成本（未扣其他运营成本）`,
              },
            ]}
          />
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <AdminChartCard title="近 7 天输入/输出 Token" option={options.llmToken} height={300} minWidth={460} />
            <AdminChartCard title="近 7 天输入/输出费用（元）" option={options.llmCost} height={300} minWidth={460} />
          </div>
          {llmUsageTop.length > 0 ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <AdminChartCard
                title="近 30 天模型 Token Top"
                option={options.llmUsageTop}
                height={horizontalBarChartHeight(Math.min(llmUsageTop.length, 10))}
                minWidth={520}
              />
              <AdminChartCard
                title="近 30 天模型费用 Top"
                subtitle="大模型 API 真实成本（元）"
                option={options.llmCostTop}
                height={horizontalBarChartHeight(Math.min(llmUsageTop.length, 10))}
                minWidth={520}
              />
            </div>
          ) : null}
          {llmUsageBySource.length > 0 ? (
            <AdminChartCard
              title="LLM 调用来源"
              subtitle="融合节点 / 辅助 Agent / 填表 AI"
              option={options.llmBySource}
              height={horizontalBarChartHeight(llmUsageBySource.length)}
              minWidth={520}
            />
          ) : null}
          <p className="text-sm text-navy-400">
            模型单价请在
            <Link to="/admin/model" className="text-gold-400/80 hover:underline mx-1">
              大模型中心
            </Link>
            调整；单价用于 Dashboard「大模型成本」核算，账单以云厂商控制台为准。
          </p>
        </div>
      )}
    </div>
  )
}
