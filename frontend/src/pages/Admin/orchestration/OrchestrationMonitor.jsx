import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Activity, BarChart3, AlertTriangle, GitBranch, Bot, Sparkles, ArrowRight } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminTabBar } from '@/components/admin/AdminUI'
import { admin } from '@/services/api'
import { resolveAgentId } from '@/utils/agentTerm'
import {
  AdminChartCard,
  EChart,
  buildAgentVolumeOption,
  buildExecutedSkippedDonutOption,
  buildHitRateBarOption,
  buildHorizontalBarOption,
} from '@/components/charts'

const AGENT_VIEWS = [
  { key: 'overview', label: '运行概览', icon: Activity },
  { key: 'stats', label: 'Sub-skill 统计', icon: BarChart3 },
]

const CONFIG_LINKS = [
  {
    to: '/admin/main-chain',
    icon: GitBranch,
    title: '主链工作室',
    desc: '步骤运营、Prompt、Tier1、模型与后处理链',
  },
  {
    to: '/admin/agent?tab=registry',
    icon: Bot,
    title: 'Agent 注册表',
    desc: '全量 Agent 定义与 JSON 高级编辑',
  },
  {
    to: '/admin/agent?tab=rules',
    icon: Sparkles,
    title: '写作规则',
    desc: 'Tier1–4 铁律，被主链步骤引用',
  },
]

function AgentConfigShortcuts({ catalog, fusionMeta }) {
  const postChain = (catalog?.post_script_chain || []).join(' → ')
  const appendAgents = (catalog?.post_script_append_agents || []).join(', ')

  return (
    <div className="space-y-4">
      <div className="glass-card rounded-2xl p-5 border border-purple-500/15 bg-purple-500/5">
        <p className="text-sm text-navy-200 leading-relaxed">
          <span className="text-white font-medium">配置与监察分离</span>
          ——本页只看全站执行健康度；改 Agent 定义、主链顺序或提示词请走各配置中心。
          Registry 当前版本 <span className="font-mono text-gold-300">{catalog?.version || '—'}</span>
          {fusionMeta?.db_version ? (
            <>
              {' · '}
              Pipeline 包 <span className="font-mono text-gold-300">{fusionMeta.db_version}</span>
              （{fusionMeta.node_count ?? 0} 步）
            </>
          ) : null}
        </p>
        {postChain ? (
          <p className="text-xs text-navy-500 mt-2">
            后处理链（Registry）：{postChain}
            {appendAgents ? ` · 追加 ${appendAgents}` : ''}
          </p>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {CONFIG_LINKS.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className="rounded-2xl border border-navy-700/40 bg-navy-900/30 p-4 hover:border-gold-500/30 hover:bg-navy-800/40 transition group"
          >
            <item.icon className="w-5 h-5 text-gold-400 mb-2" />
            <div className="text-sm font-semibold text-white group-hover:text-gold-200">{item.title}</div>
            <p className="text-xs text-navy-500 mt-1 leading-relaxed">{item.desc}</p>
            <span className="inline-flex items-center gap-1 text-[11px] text-gold-400/80 mt-2">
              去配置
              <ArrowRight className="w-3 h-3" />
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}

function SubSkillStatsPanel({ stats, statsByAgent, compact = false }) {
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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          { label: '轨迹样本', value: stats?.sample_size ?? 0 },
          { label: '覆盖项目', value: stats?.project_count ?? 0 },
          { label: '总执行', value: totals.executed, tone: 'text-green-400' },
          { label: '活跃 Agent', value: statsByAgent.length },
        ].map((card) => (
          <div key={card.label} className="rounded-xl bg-navy-800/50 px-4 py-3 border border-navy-700/30">
            <p className="text-[10px] text-navy-500">{card.label}</p>
            <p className={`text-xl font-bold mt-0.5 ${card.tone || 'text-white'}`}>{card.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3 mb-6">
        <div className="rounded-xl bg-navy-800/30 border border-navy-700/30 p-4 lg:col-span-2">
          <p className="text-xs text-navy-400 mb-2">各 Agent 执行量</p>
          <EChart option={volumeOption} height={220} />
        </div>
        <div className="rounded-xl bg-navy-800/30 border border-navy-700/30 p-4">
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
              className="!p-4 !bg-navy-800/30 border border-navy-700/30"
            />
            <AdminChartCard
              title="各 Agent 平均执行率"
              option={hitRateOption}
              height={260}
              className="!p-4 !bg-navy-800/30 border border-navy-700/30"
            />
          </div>

          <p className="text-xs text-navy-500 mb-3">
            执行率 = 实际执行 ÷（执行 + 跳过 + 失败）。偏低通常表示编排里该步常被跳过，或前置条件未满足。
          </p>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {enrichedGroups.map((group) => (
              <div
                key={group.agent_id}
                className="rounded-xl bg-navy-800/40 border border-navy-700/30 p-3"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="min-w-0">
                    <p className="text-sm text-white font-medium truncate">
                      {group.agent_name || group.agent_id}
                    </p>
                    <p className="text-[10px] text-navy-500 font-mono">
                      {group.agent_id}
                    </p>
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
                <p className="text-[10px] text-navy-500 mb-2">
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
              </div>
            ))}
          </div>
        </>
      ) : (
        <AdminChartCard
          title="执行次数 Top 子技能"
          option={topSkillsOption}
          height={240}
          className="!p-4 !bg-navy-800/30 border border-navy-700/30"
        />
      )}
    </>
  )
}

function OrchestrationStatsKpi({ stats, statsByAgent }) {
  const totals = useMemo(() => {
    let executed = 0
    for (const g of statsByAgent) {
      for (const s of g.skills) {
        executed += s.executed || 0
      }
    }
    return { executed }
  }, [statsByAgent])

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {[
        { label: '轨迹样本', value: stats?.sample_size ?? 0 },
        { label: '覆盖项目', value: stats?.project_count ?? 0 },
        { label: '总执行', value: totals.executed, tone: 'text-green-400' },
        { label: '活跃 Agent', value: statsByAgent.length },
      ].map((card) => (
        <div key={card.label} className="rounded-xl bg-navy-800/50 px-4 py-3 border border-navy-700/30">
          <p className="text-[10px] text-navy-500">{card.label}</p>
          <p className={`text-xl font-bold mt-0.5 ${card.tone || 'text-white'}`}>{card.value}</p>
        </div>
      ))}
    </div>
  )
}

function AgentOverviewPanel({
  stats,
  statsByAgent,
  statsLoading,
  onOpenStats,
}) {
  const lowHitAgents = statsByAgent.filter((g) => {
    const avg =
      g.skills.length > 0
        ? g.skills.reduce((s, r) => s + (r.hit_rate || 0), 0) / g.skills.length
        : 0
    return avg < 0.5 && g.skills.some((s) => (s.executed || 0) + (s.skipped || 0) > 3)
  })

  return (
    <div className="space-y-6">
      <div className="glass-card rounded-2xl p-5 border border-blue-500/15 bg-blue-500/5">
        <p className="text-sm text-navy-200 leading-relaxed">
          <span className="text-white font-medium">全站 Agent 健康度</span>
          — 汇总近期项目的子技能执行、跳过与失败。单项目逐步结果见
          <Link to="/admin/creation/projects" className="text-gold-400 hover:underline mx-1">
            创作项目 → 轨迹
          </Link>
          。
        </p>
      </div>

      {statsLoading ? (
        <p className="text-sm text-navy-400">加载统计…</p>
      ) : statsByAgent.length === 0 ? (
        <p className="text-sm text-navy-500">暂无数据（需有项目跑过工作台后才会出现）</p>
      ) : (
        <OrchestrationStatsKpi stats={stats} statsByAgent={statsByAgent} />
      )}

      {lowHitAgents.length > 0 ? (
        <div className="rounded-2xl border border-amber-500/25 bg-amber-500/5 p-4">
          <p className="text-sm text-amber-200 flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4" />
            执行率偏低的 Agent（&lt;50%，且样本 &gt;3）
          </p>
          <ul className="text-xs text-navy-300 space-y-1">
            {lowHitAgents.slice(0, 5).map((g) => (
              <li key={g.agent_id}>
                {g.agent_name || g.agent_id}
                <span className="text-navy-500 ml-1 font-mono">
                  ({g.agent_id})
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3 text-sm">
        <button
          type="button"
          onClick={onOpenStats}
          className="px-4 py-2 rounded-xl bg-gold-500/15 text-gold-300 border border-gold-500/30 hover:bg-gold-500/25"
        >
          查看完整 Sub-skill 统计
        </button>
        <Link
          to="/admin/creation/projects?failed_run=1"
          className="px-4 py-2 rounded-xl text-navy-200 border border-navy-600/40 hover:bg-navy-800/50"
        >
          有失败 run 的项目
        </Link>
      </div>
    </div>
  )
}

export default function OrchestrationMonitor() {
  const [searchParams, setSearchParams] = useSearchParams()
  const view = searchParams.get('view') || 'overview'

  const [catalog, setCatalog] = useState(null)
  const [fusionMeta, setFusionMeta] = useState(null)
  const [stats, setStats] = useState(null)
  const [statsLoading, setStatsLoading] = useState(true)
  const [error, setError] = useState('')

  const switchView = (key) => {
    setSearchParams({ view: key }, { replace: true })
  }

  useEffect(() => {
    Promise.all([
      admin.agentCatalog().then(setCatalog).catch((e) => {
        setError(e.message || '加载 Registry 快照失败')
      }),
      admin.getFusionMeta().then(setFusionMeta).catch(() => setFusionMeta(null)),
    ]).catch(() => {})

    admin
      .agentSubSkillStats(300)
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setStatsLoading(false))
  }, [])

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

  return (
    <AdminShell
      title="调度监控"
      description="全站执行健康度与 sub-skill 统计；Agent 定义与主链配置见各中心"
      actions={
        <Link to="/admin/main-chain" className="text-sm text-gold-400 hover:text-gold-300">
          主链工作室
        </Link>
      }
    >
      {error && !catalog ? (
        <div className="mb-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          {error}
        </div>
      ) : null}

      <AgentConfigShortcuts catalog={catalog} fusionMeta={fusionMeta} />

      <AdminTabBar tabs={AGENT_VIEWS} active={view} onChange={switchView} />

      {view === 'overview' ? (
        <AgentOverviewPanel
          stats={stats}
          statsByAgent={statsByAgent}
          statsLoading={statsLoading}
          onOpenStats={() => switchView('stats')}
        />
      ) : null}

      {view === 'stats' ? (
        <section className="rounded-2xl border border-navy-700/40 bg-navy-900/30 p-5 space-y-6">
          <div>
            <h2 className="text-sm font-semibold text-gold-400 mb-1 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              全站 Sub-skill 统计
            </h2>
            <p className="text-xs text-navy-500 mb-3">
              执行率 = 实际执行 ÷（执行 + 跳过 + 失败）；失败单独统计在 DB 与项目监察中。
            </p>
            {statsLoading ? (
              <p className="text-sm text-navy-400">加载中…</p>
            ) : skillStats.length === 0 ? (
              <p className="text-sm text-navy-500">暂无数据</p>
            ) : (
              <SubSkillStatsPanel stats={stats} statsByAgent={statsByAgent} />
            )}
          </div>
        </section>
      ) : null}
    </AdminShell>
  )
}
