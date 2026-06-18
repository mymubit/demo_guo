import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Bot, Activity, Route } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminPageHeader, AdminPillTabs } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import IndependentAgentPanel from './IndependentAgentPanel'
import AgentLlmRoutePanel from './AgentLlmRoutePanel'
import AgentRunsPanel from './AgentRunsPanel'

const AGENT_TABS = [
  { key: 'definitions', label: '定义', icon: Bot },
  { key: 'runs', label: '运行记录', icon: Activity },
  { key: 'routes', label: '路由', icon: Route },
]

export default function AgentHubPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'definitions'
  const legacyTabMap = {
    catalog: 'definitions',
    form: 'definitions',
    review: 'definitions',
    rules: 'skills-rules',
  }
  const resolvedTab = legacyTabMap[tab] || tab

  useEffect(() => {
    if (tab === 'rules') {
      navigate('/admin/skills?tab=rules', { replace: true })
    }
  }, [tab, navigate])

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
        crumbs={[{ label: 'Console' }, { label: 'AI 配置' }, { label: 'Agent' }]}
        title="Agent 定义 · 运行 · 路由"
        subtitle="独立 Agent Prompt、LLM 路由与健康检查 · Tier 规则已迁至技能页"
      />
      <AdminPillTabs tabs={AGENT_TABS} active={active.key} onChange={switchTab} className="w-full" />
      <MessageBanner />
      {active.key === 'definitions' ? <IndependentAgentPanel onMessage={showMessage} /> : null}
      {active.key === 'runs' ? <AgentRunsPanel /> : null}
      {active.key === 'routes' ? <AgentLlmRoutePanel onMessage={showMessage} /> : null}
    </AdminShell>
  )
}
