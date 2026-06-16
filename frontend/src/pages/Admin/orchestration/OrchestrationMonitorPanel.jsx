import { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, ExternalLink, Play, RefreshCw, Activity } from 'lucide-react'
import { AdminEmpty, AdminLoading, AdminPanel, KpiTile } from '@/components/admin/AdminUI'
import { ICON } from '@/constants/iconSizes'
import { cn } from '@/utils/cn'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import { admin } from '@/services/api'
import { resolveAgentId } from '@/utils/agentTerm'
import OrchestrationReplayPanel from '@/components/admin/OrchestrationReplayPanel'
import OrchestrationNodeStateBadge from '@/components/admin/OrchestrationNodeStateBadge'
import { useOrchestrationHubContext } from './OrchestrationHubContext'
import {
  AdminChartCard,
  EChart,
  buildAgentVolumeOption,
  buildExecutedSkippedDonutOption,
  buildHitRateBarOption,
  buildHorizontalBarOption,
} from '@/components/charts'

function QueueStat({ label, value, tone }) {
  const toneClass =
    tone === 'success'
      ? 'text-success-300'
      : tone === 'danger'
        ? 'text-danger-300'
        : tone === 'info'
          ? 'text-info-300'
          : tone === 'warning'
            ? 'text-warning-300'
            : 'text-white'
  return (
    <div className="rounded-md border border-white/5 bg-white/[0.02] px-2 py-1.5">
      <div className="text-[10px] text-slate-500">{label}</div>
      <div className={cn('text-sm font-bold', toneClass)}>{value}</div>
    </div>
  )
}

function SubSkillStatsPanel({ stats, statsByAgent, onAgentClick, compact = false }) {
  const totals = useMemo(() => {
    let executed = 0
    let skipped = 0
    for (const g of statsByAgent) {
      for (const s of g.skills) {
        executed += s.executed || 0
        skipped += s.skipped || 0
      }
    }
    return { executed, skipped }
  }, [statsByAgent])

  const enrichedGroups = useMemo(
    () =>
      statsByAgent.map((g) => ({
        ...g,
        executedTotal: g.skills.reduce((s, r) => s + (r.executed || 0), 0),
        skippedTotal: g.skills.reduce((s, r) => s + (r.skipped || 0), 0),
        avgHitRate:
          g.skills.length > 0
            ? g.skills.reduce((s, r) => s + (r.hit_rate || 0), 0) / g.skills.length
            : 0,
      })),
    [statsByAgent],
  )

  const volumeOption = useMemo(() => buildAgentVolumeOption({ groups: enrichedGroups }), [enrichedGroups])
  const donutOption = useMemo(
    () => buildExecutedSkippedDonutOption({ executed: totals.executed, skipped: totals.skipped }),
    [totals],
  )
  const topSkillsOption = useMemo(() => {
    const all = statsByAgent.flatMap((g) =>
      g.skills.map((s) => ({
        display_name: `${g.agent_name || g.agent_id} · ${s.skill_id}`,
        call_count: s.executed || 0,
      })),
    )
    return buildHorizontalBarOption({
      rows: all.sort((a, b) => b.call_count - a.call_count).slice(0, 8),
      valueKey: 'call_count',
      labelKey: 'display_name',
      valueSuffix: ' 次',
      color: '#a855f7',
      maxItems: 8,
    })
  }, [statsByAgent])
  const hitRateOption = useMemo(
    () =>
      buildHitRateBarOption({
        rows: enrichedGroups.map((g) => ({
          label: g.agent_name || g.agent_id,
          rate: g.avgHitRate,
        })),
        labelKey: 'label',
        rateKey: 'rate',
      }),
    [enrichedGroups],
  )

  return (
    <>
      <div className="grid gap-4 lg:grid-cols-3 mb-6">
        <div className="rounded-xl border border-white/5 bg-slate-900/40 p-4 lg:col-span-2">
          <p className="text-xs text-navy-400 mb-2">各 Agent 执行量</p>
          <EChart option={volumeOption} height={220} />
        </div>
        <div className="rounded-xl border border-white/5 bg-slate-900/40 p-4">
          <p className="text-xs text-navy-400 mb-2">全站执行 / 跳过 / 失败占比</p>
          <EChart option={donutOption} height={220} />
        </div>
      </div>

      {!compact ? (
        <>
          <div className="grid gap-4 lg:grid-cols-2 mb-6">
            <AdminChartCard
              title="执行次数 Top 子技能"
              option={topSkillsOption}
              height={260}
              className="!p-4 border border-white/5 !bg-slate-900/40"
            />
            <AdminChartCard
              title="各 Agent 平均执行率"
              option={hitRateOption}
              height={260}
              className="!p-4 border border-white/5 !bg-slate-900/40"
            />
          </div>

          <p className="text-xs text-navy-400 mb-3">
            点击 Agent 卡片可跳转流程编排并高亮对应节点。
          </p>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {enrichedGroups.map((group) => (
              <button
                key={group.agent_id}
                type="button"
                onClick={() => onAgentClick?.(group.agent_id)}
                className="rounded-xl border border-white/5 bg-slate-900/40 p-3 text-left transition-colors hover:border-gold-500/25 hover:bg-white/[0.05]"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="min-w-0">
                    <p className="text-sm text-white font-medium truncate">
                      {group.agent_name || group.agent_id}
                    </p>
                    <p className="text-[10px] text-navy-300 font-mono">{group.agent_id}</p>
                  </div>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full shrink-0 ${
                      group.avgHitRate >= 0.8
                        ? 'bg-green-500/15 text-green-400'
                        : group.avgHitRate >= 0.5
                          ? 'bg-gold-500/15 text-gold-400'
                          : 'bg-red-500/15 text-red-400'
                    }`}
                  >
                    均执行率 {Math.round(group.avgHitRate * 100)}%
                  </span>
                </div>
                <p className="text-[10px] text-navy-400 mb-2">
                  执行 {group.executedTotal} · 跳过 {group.skippedTotal}
                  {(group.skills.reduce((s, r) => s + (r.failed || 0), 0) || 0) > 0
                    ? ` · 失败 ${group.skills.reduce((s, r) => s + (r.failed || 0), 0)}`
                    : ''}
                </p>
                <EChart
                  option={buildHitRateBarOption({
                    rows: [...group.skills]
                      .sort((a, b) => (b.executed || 0) - (a.executed || 0))
                      .slice(0, 6)
                      .map((s) => ({ label: s.skill_id, rate: s.hit_rate || 0 })),
                    labelKey: 'label',
                    rateKey: 'rate',
                  })}
                  height={Math.max(120, Math.min(group.skills.length, 6) * 28)}
                />
              </button>
            ))}
          </div>
        </>
      ) : (
        <AdminChartCard
          title="执行次数 Top 子技能"
          option={topSkillsOption}
          height={240}
          className="!p-4 border border-white/5 !bg-slate-900/40"
        />
      )}
    </>
  )
}

function RecentRunsPanel({ runs = [], nodeStates = {}, onReplay, onLocateAgent }) {
  if (!runs.length) {
    return <p className="text-sm text-navy-400">暂无近期执行记录</p>
  }

  return (
    <div className="space-y-2">
      {runs.slice(0, 12).map((run) => {
        const state =
          run.status === 'running'
            ? 'running'
            : run.status === 'failed'
              ? 'failed'
              : run.status === 'completed' || run.status === 'partial'
                ? 'completed'
                : 'idle'
        return (
          <div
            key={run.id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/5 bg-slate-900/40 px-3 py-2.5"
          >
            <div className="min-w-0">
              <p className="text-sm text-white truncate">{run.project_title || '项目'}</p>
              <p className="text-xs text-navy-400 mt-0.5">
                {run.agent_id}
                {run.fusion_node_id ? (
                  <span className="font-mono text-navy-300 ml-1">· {run.fusion_node_id}</span>
                ) : null}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <OrchestrationNodeStateBadge state={state} />
              <button
                type="button"
                onClick={() => onReplay?.(run.id)}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] text-navy-200 border border-white/10 hover:bg-white/[0.06]"
              >
                <Play className="w-3 h-3" />
                回放
              </button>
              {run.fusion_node_id || run.agent_id ? (
                <button
                  type="button"
                  onClick={() => onLocateAgent?.(run.agent_id, run.fusion_node_id)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] text-gold-300 border border-gold-500/25 hover:bg-gold-500/10"
                >
                  <ExternalLink className="w-3 h-3" />
                  定位
                </button>
              ) : null}
            </div>
          </div>
        )
      })}
      {Object.keys(nodeStates).length ? (
        <p className="text-[11px] text-navy-500 pt-1">
          节点运行态已同步 {Object.keys(nodeStates).length} 个步骤（来自近期 Run）
        </p>
      ) : null}
    </div>
  )
}

export default function OrchestrationMonitorPanel() {
  const hub = useOrchestrationHubContext()
  const { highlightAgent, highlightStep, openReplay, closeReplay, replayRunId, steps = [] } = hub || {}
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  const [stats, setStats] = useState(null)
  const [recentRuns, setRecentRuns] = useState([])
  const [nodeStates, setNodeStates] = useState({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)

  const load = useCallback(async () => {
    setLoadError(null)
    setLoading(true)
    try {
      const [skillStats, recent] = await Promise.all([
        admin.agentSubSkillStats(300),
        admin.orchestrationRecentRuns(40),
      ])
      setStats(skillStats)
      setRecentRuns(recent?.runs || [])
      setNodeStates(recent?.node_states || {})
    } catch (err) {
      setLoadError(err)
      setStats(null)
      setRecentRuns([])
      showMessage(err.message || '加载统计数据失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [showMessage])

  useEffect(() => {
    load()
    // 自动轮询：每 10 秒刷新监察数据
    const timer = setInterval(() => { load() }, 10_000)
    return () => clearInterval(timer)
  }, [load])

  const skillStats = stats?.skills || []

  const statsByAgent = useMemo(() => {
    const groups = {}
    for (const row of skillStats) {
      const agentId = resolveAgentId(row)
      const key = agentId || row.agent_name
      if (!groups[key]) {
        groups[key] = {
          agent_id: agentId,
          agent_name: row.agent_name || agentId,
          skills: [],
        }
      }
      groups[key].skills.push(row)
    }
    return Object.values(groups)
  }, [skillStats])

  const lowHitAgents = statsByAgent.filter((g) => {
    const avg =
      g.skills.length > 0
        ? g.skills.reduce((s, r) => s + (r.hit_rate || 0), 0) / g.skills.length
        : 0
    return avg < 0.5 && g.skills.some((s) => (s.executed || 0) + (s.skipped || 0) > 3)
  })

  const runMetrics = useMemo(() => {
    const running = recentRuns.filter((r) => r.status === 'running').length
    const failed = recentRuns.filter((r) => r.status === 'failed').length
    const completed = recentRuns.filter((r) => ['completed', 'partial'].includes(r.status)).length
    const total = recentRuns.length
    const failRate = total ? `${((failed / total) * 100).toFixed(1)}%` : '0%'
    return { running, failed, completed, total, failRate }
  }, [recentRuns])

  const agentQueues = useMemo(
    () =>
      statsByAgent.map((g) => {
        const executed = g.skills.reduce((s, r) => s + (r.executed || 0), 0)
        const skipped = g.skills.reduce((s, r) => s + (r.skipped || 0), 0)
        const failed = g.skills.reduce((s, r) => s + (r.failed || 0), 0)
        return {
          id: g.agent_id || g.agent_name,
          name: g.agent_name || g.agent_id,
          executed,
          skipped,
          failed,
        }
      }),
    [statsByAgent],
  )

  if (loading && stats === null && !loadError) {
    return <AdminLoading label="加载调度数据…" />
  }

  if (loadError && stats === null) {
    return (
      <div className="space-y-4">
        <MessageBanner />
        <AdminEmpty title="调度数据加载失败" description={loadError.message || '请稍后重试'} />
        <div className="flex justify-center">
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? '重试中…' : '重新加载'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <MessageBanner />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-400 leading-relaxed">
          点击 Agent / Run 可跳转编排页高亮节点，或逐步回放子技能。
        </p>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-slate-200 border border-white/10 hover:bg-white/5 disabled:opacity-60"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </button>
      </div>

      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="正在运行" value={String(runMetrics.running)} />
        <KpiTile label="近期完成" value={String(runMetrics.completed)} />
        <KpiTile label="轨迹样本" value={String(stats?.sample_size ?? 0)} gold />
        <KpiTile
          label="失败率"
          value={runMetrics.failRate}
          danger={runMetrics.failed > 0}
          hint={runMetrics.total ? `样本 ${runMetrics.total} 条` : undefined}
        />
      </div>

      {agentQueues.length > 0 ? (
        <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2 lg:grid-cols-4">
          {agentQueues.slice(0, 8).map((q) => (
            <button
              key={q.id}
              type="button"
              onClick={() => highlightAgent?.(q.id)}
              className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5 text-left transition-colors hover:border-white/10"
            >
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-400 truncate">{q.name}</div>
                <Activity className={cn(ICON.md, 'text-indigo-400 shrink-0')} />
              </div>
              <div className="mt-1.5 font-mono text-[10px] text-slate-500 truncate">{q.id}</div>
              <div className="mt-3 grid grid-cols-2 gap-1.5 text-xs">
                <QueueStat label="执行" value={q.executed} tone="info" />
                <QueueStat label="跳过" value={q.skipped} />
                <QueueStat label="失败" value={q.failed} tone={q.failed > 2 ? 'danger' : 'warning'} />
                <QueueStat
                  label="技能数"
                  value={statsByAgent.find((g) => (g.agent_id || g.agent_name) === q.id)?.skills.length ?? 0}
                />
              </div>
            </button>
          ))}
        </div>
      ) : null}

      {replayRunId ? (
        <OrchestrationReplayPanel
          runId={replayRunId}
          steps={steps}
          onClose={closeReplay}
          onLocateNode={(nodeId) => highlightStep?.(nodeId)}
          onOpenFlow={(nodeId) => {
            if (nodeId) highlightStep?.(nodeId)
            else highlightAgent?.(recentRuns.find((r) => r.id === replayRunId)?.agent_id)
          }}
        />
      ) : null}

      {lowHitAgents.length > 0 ? (
        <div className="rounded-2xl border border-amber-500/25 bg-amber-500/5 p-4">
          <p className="text-sm text-amber-200 flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4" />
            执行率偏低的 Agent（&lt;50%，且样本 &gt;3）
          </p>
          <ul className="text-xs text-navy-300 space-y-1">
            {lowHitAgents.slice(0, 5).map((g) => (
              <li key={g.agent_id}>
                <button
                  type="button"
                  onClick={() => highlightAgent?.(g.agent_id)}
                  className="hover:text-gold-300 transition-colors"
                >
                  {g.agent_name || g.agent_id}
                  <span className="text-navy-300 ml-1 font-mono">({g.agent_id})</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <AdminPanel title="近期执行" sub="按时间倒序 · 支持回放与节点定位">
        <RecentRunsPanel
          runs={recentRuns}
          nodeStates={nodeStates}
          onReplay={(runId) => openReplay?.(runId)}
          onLocateAgent={(agentId, fusionNodeId) => {
            if (fusionNodeId) highlightStep?.(fusionNodeId)
            else highlightAgent?.(agentId)
          }}
        />
      </AdminPanel>

      {skillStats.length > 0 ? (
        <AdminPanel title="Sub-skill 统计" sub="各 Agent 子技能执行量与健康度">
          {loading ? (
            <p className="text-sm text-slate-400">加载中…</p>
          ) : (
            <SubSkillStatsPanel
              stats={stats}
              statsByAgent={statsByAgent}
              onAgentClick={(agentId) => highlightAgent?.(agentId)}
            />
          )}
        </AdminPanel>
      ) : null}
    </div>
  )
}
