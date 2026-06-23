import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bot,
  FolderKanban,
  SlidersHorizontal,
  BarChart3,
  Cpu,
} from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminStatGrid, AdminLoading } from '@/components/admin/AdminUI'
import { admin } from '@/services/api'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const HUB_CARDS = [
  {
    to: '/admin/agent',
    icon: Bot,
    title: 'Agent 中心',
    desc: 'Drama 36 角色 Prompt 定义、Knowledge 与 LLM 路由',
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
    to: '/admin/agent?tab=definitions',
    icon: BarChart3,
    title: '运行记录',
    desc: 'Drama 角色最近执行与健康状态',
    accent: 'from-purple-500/20 to-purple-600/5 border-purple-500/25',
  },
  {
    to: '/admin/portal',
    icon: SlidersHorizontal,
    title: '配置中心',
    desc: '创作表单、题材与钩子库（填表 Agent → Agent 中心）',
    accent: 'from-gold-500/20 to-gold-600/5 border-gold-500/25',
  },
]

export function CreationCenterPage() {
  const [loading, setLoading] = useState(true)
  const [agentOps, setAgentOps] = useState({})
  const [summary, setSummary] = useState({})
  const [opsAlerts, setOpsAlerts] = useState({})

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
  }, [])

  const execToday = agentOps.execution?.summary?.today || {}

  return (
    <AdminShell>
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
                label: 'Drama 项目',
                value: agentOps.workspace_projects ?? agentOps.workspace_project_count ?? summary.creation_projects ?? 0,
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
          <p className="text-xs text-navy-400">
            Agent 执行记录 →
            <Link to="/admin/agent?tab=runs" className="text-gold-400 hover:underline mx-1">
              角色运行记录
            </Link>
          </p>
        </div>
      )}

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
              {renderLucideIcon(card.icon, 'w-5 h-5 text-gold-400 mb-3')}
              <h3 className="text-white font-semibold mb-1">{card.title}</h3>
              <p className="text-xs text-navy-400 leading-relaxed">{card.desc}</p>
            </Link>
          )
        })}
      </div>

      <p className="text-xs text-navy-400">
        Agent 配置与 LLM 路由见
        <Link to="/admin/agent" className="text-gold-400/80 hover:underline mx-1">
          Agent 中心
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

/** @deprecated 已迁移至 AgentHubPage / ModelHubPage */
export function AiPipelineHubPage() {
  return null
}
