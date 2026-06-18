import { useSearchParams } from 'react-router-dom'
import { Bot, Activity, Route, BookOpen } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminPageHeader, AdminPillTabs } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import IndependentAgentPanel from './IndependentAgentPanel'
import SkillRulesPanel from './SkillRulesPanel'
import AgentLlmRoutePanel from './AgentLlmRoutePanel'
import AgentRunsPanel from './AgentRunsPanel'

const AGENT_TABS = [
  { key: 'definitions', label: '定义', icon: Bot },
  { key: 'runs', label: '运行记录', icon: Activity },
  { key: 'routes', label: '路由', icon: Route },
  { key: 'rules', label: '规则', icon: BookOpen },
]

export default function AgentHubPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'definitions'
  const legacyTabMap = {
    catalog: 'definitions',
    form: 'definitions',
    review: 'definitions',
  }
  const resolvedTab = legacyTabMap[tab] || tab
  const active = AGENT_TABS.find((t) => t.key === resolvedTab) || AGENT_TABS[0]
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  const switchTab = (key) => {
    const next = new URLSearchParams(searchParams)
    next.set('tab', key)
    next.delete('action')
    setSearchParams(next, { replace: true })
  }

  return (
    <AdminShell hideDescription>
      <AdminPageHeader
        crumbs={[{ label: 'Console' }, { label: 'Agent 中心' }]}
        title="Agent 定义 · 运行 · 路由 · 规则"
        subtitle="独立 Agent Prompt、LLM 路由与健康检查"
      />
      <AdminPillTabs tabs={AGENT_TABS} active={active.key} onChange={switchTab} className="w-full" />
      <MessageBanner />
      {active.key === 'definitions' ? <IndependentAgentPanel onMessage={showMessage} /> : null}
      {active.key === 'runs' ? <AgentRunsPanel /> : null}
      {active.key === 'rules' ? <SkillRulesPanel onMessage={showMessage} /> : null}
      {active.key === 'routes' ? <AgentLlmRoutePanel onMessage={showMessage} /> : null}
    </AdminShell>
  )
}
