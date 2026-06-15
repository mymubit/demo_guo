import { Link, useSearchParams } from 'react-router-dom'
import { Bot, Sparkles, Gauge, Route } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminTabBar } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import AgentRegistryPanel from './AgentRegistryPanel'
import SkillRulesPanel from './SkillRulesPanel'
import ReviewScoringPanel from './ReviewScoringPanel'
import AgentLlmRoutePanel from './AgentLlmRoutePanel'

const AGENT_TABS = [
  {
    key: 'registry',
    label: 'Agent 注册表',
    icon: Bot,
    hint: 'Agent 定义与 JSON 高级；步骤 Prompt 见主链工作室',
  },
  {
    key: 'rules',
    label: '规则库',
    icon: Sparkles,
    hint: 'Tier1–4 铁律与节点规则，被主链步骤引用。',
  },
  {
    key: 'review',
    label: '质检评分',
    icon: Gauge,
    hint: 'Review / Score 策略与通过线。',
  },
  {
    key: 'routes',
    label: 'LLM 路由',
    icon: Route,
    hint: '各 Agent 阶段的 Provider 与 Max Tokens。',
  },
]

export default function AgentHubPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'registry'
  const active = AGENT_TABS.find((t) => t.key === tab) || AGENT_TABS[0]
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  const switchTab = (key) => {
    setSearchParams({ tab: key }, { replace: true })
  }

  return (
    <AdminShell
      title="Agent 中心"
      description="写作规则、质检策略与高级 Registry；日常主链配置请用主链工作室"
    >
      <div className="glass-card rounded-2xl p-4 border border-gold-500/15 bg-gold-500/5 mb-4">
        <p className="text-sm text-navy-200">
          日常配置请优先使用
          <Link to="/admin/main-chain" className="text-gold-400 hover:underline mx-1">
            主链工作室
          </Link>
          （步骤 Inspector 已含 Prompt / Tier1 / 子技能 / 模型）。
        </p>
      </div>
      <AdminTabBar tabs={AGENT_TABS} active={active.key} onChange={switchTab} />
      <p className="text-xs text-navy-500 -mt-2">{active.hint}</p>
      <MessageBanner />
      {active.key === 'registry' ? <AgentRegistryPanel onMessage={showMessage} /> : null}
      {active.key === 'rules' ? <SkillRulesPanel onMessage={showMessage} /> : null}
      {active.key === 'review' ? <ReviewScoringPanel onMessage={showMessage} /> : null}
      {active.key === 'routes' ? <AgentLlmRoutePanel onMessage={showMessage} /> : null}
    </AdminShell>
  )
}
