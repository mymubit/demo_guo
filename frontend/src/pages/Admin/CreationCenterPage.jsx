import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bot,
  GitBranch,
  FolderKanban,
  SlidersHorizontal,
  BarChart3,
  ArrowRight,
  Cpu,
} from 'lucide-react'
import CreationPipelineDiagram from '@/components/admin/CreationPipelineDiagram'
import AdminShell from '@/components/admin/AdminShell'
import { AdminStatGrid, AdminLoading } from '@/components/admin/AdminUI'
import { admin } from '@/services/api'

const HUB_CARDS = [
  {
    to: '/admin/main-chain',
    icon: GitBranch,
    title: '主链工作室',
    desc: '主链蓝图、步骤运营、Prompt 与模型路由',
    accent: 'from-blue-500/20 to-blue-600/5 border-blue-500/25',
  },
  {
    to: '/admin/agent',
    icon: Bot,
    title: 'Agent 中心',
    desc: '注册表、规则库、质检评分与 LLM 路由',
    accent: 'from-indigo-500/20 to-indigo-600/5 border-indigo-500/25',
  },
  {
    to: '/admin/model',
    icon: Cpu,
    title: '模型中心',
    desc: '厂商 Key、模型目录与 Token 单价',
    accent: 'from-cyan-500/20 to-cyan-600/5 border-cyan-500/25',
  },
  {
    to: '/admin/creation/projects',
    icon: FolderKanban,
    title: '创作项目',
    desc: '全站项目列表、侧栏轨迹与完整监察页',
    accent: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/25',
    alertKey: 'has_failed_run',
  },
  {
    to: '/admin/orchestration?view=overview',
    icon: BarChart3,
    title: '调度监控',
    desc: '全站 sub-skill 命中率与失败分布',
    accent: 'from-purple-500/20 to-purple-600/5 border-purple-500/25',
  },
  {
    to: '/admin/portal',
    icon: SlidersHorizontal,
    title: '配置中心',
    desc: '创作表单、填表 AI、题材与钩子库',
    accent: 'from-gold-500/20 to-gold-600/5 border-gold-500/25',
  },
]

export function CreationCenterPage() {
  const [loading, setLoading] = useState(true)
  const [agentOps, setAgentOps] = useState({})
  const [summary, setSummary] = useState({})
  const [opsAlerts, setOpsAlerts] = useState({})
  const [blueprint, setBlueprint] = useState(null)

  useEffect(() => {
    admin
      .getDashboard()
      .then((dash) => {
        setAgentOps(dash?.agent_ops || {})
        setSummary(dash?.summary || {})
        setOpsAlerts(dash?.ops_alerts || {})
      })
      .catch(() => {})
      .finally(() => setLoading(false))
    admin.getMainChainBlueprint().then(setBlueprint).catch(() => {})
  }, [])

  const execToday = agentOps.execution?.summary?.today || {}

  return (
    <AdminShell
      title="创作中心"
      description="按「配置 → 监察 → 内容」组织创作运营；下方入口对应十大中心快捷路径"
    >
      {loading ? (
        <AdminLoading label="加载运营概览…" />
      ) : (
        <div className="space-y-4">
          {(opsAlerts.has_failed_run ?? 0) > 0 ? (
            <div className="rounded-xl border border-amber-500/25 bg-amber-500/5 px-4 py-3 flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-amber-200">
                近 7 天有 <strong>{opsAlerts.has_failed_run}</strong> 个项目存在失败 Agent 执行
              </p>
              <Link
                to="/admin/creation/projects?failed_run=1"
                className="text-xs text-gold-400 hover:text-gold-300"
              >
                查看项目 →
              </Link>
            </div>
          ) : null}
          <AdminStatGrid
            columns={3}
            items={[
              {
                label: '工作台项目',
                value: agentOps.workspace_projects ?? summary.creation_projects ?? 0,
              },
              {
                label: '今日 Agent 执行',
                value: execToday.run_count ?? 0,
                hint: execToday.run_count
                  ? `失败 ${execToday.failed_count ?? 0}`
                  : '详见数据概览',
              },
              {
                label: '轨迹覆盖项目',
                value: agentOps.trace_project_count ?? 0,
                hint: `样本 ${agentOps.trace_sample_size ?? 0} 条`,
              },
            ]}
          />
          <p className="text-xs text-navy-500">
            Sub-skill 命中率与失败分布 →
            <Link to="/admin/orchestration?view=stats" className="text-gold-400 hover:underline mx-1">
              调度监控
            </Link>
          </p>
        </div>
      )}

      <div className="glass-card rounded-2xl p-5 border border-navy-700/30">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div>
            <h2 className="text-sm font-semibold text-white">创作流水线</h2>
            <p className="text-xs text-navy-500 mt-0.5">
              改编预处理 → 工作台五步 → 后处理链（审查 / 润色 / 评分 / 营销 / 洞察）
            </p>
          </div>
          <Link
            to="/admin/main-chain"
            className="text-xs text-gold-400 hover:text-gold-300 inline-flex items-center gap-1"
          >
            去配置
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        <CreationPipelineDiagram linkTo="/admin/main-chain" blueprint={blueprint} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {HUB_CARDS.map((card) => {
          const alertCount = card.alertKey ? opsAlerts[card.alertKey] : 0
          return (
            <Link
              key={card.to}
              to={card.to}
              className={`relative rounded-2xl border p-5 bg-gradient-to-br transition hover:ring-1 hover:ring-gold-500/25 ${card.accent}`}
            >
              {alertCount > 0 ? (
                <span className="absolute top-3 right-3 min-w-[1.25rem] px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/25 text-amber-100 text-center">
                  {alertCount}
                </span>
              ) : null}
              <card.icon className="w-5 h-5 text-gold-400 mb-3" />
              <h3 className="text-white font-semibold mb-1">{card.title}</h3>
              <p className="text-xs text-navy-400 leading-relaxed">{card.desc}</p>
            </Link>
          )
        })}
      </div>

      <p className="text-xs text-navy-500">
        主链步骤扣费在
        <Link to="/admin/main-chain" className="text-gold-400/80 hover:underline mx-1">
          主链工作室
        </Link>
        ；币种与注册赠送在
        <Link to="/admin/commerce/settings" className="text-gold-400/80 hover:underline mx-1">
          商业 · 钱包
        </Link>
        。
      </p>
    </AdminShell>
  )
}

/** @deprecated 已迁移至 MainChainStudioPage / AgentHubPage / ModelHubPage */
export function AiPipelineHubPage() {
  return null
}
