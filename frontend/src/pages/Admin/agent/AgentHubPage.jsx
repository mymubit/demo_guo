import { useSearchParams } from 'react-router-dom'
import { Bot, LayoutGrid, Sparkles, Gauge, Route, BookOpen, Activity } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminPageHeader, AdminPillTabs } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import AdminAgentCatalogPanel from './AdminAgentCatalogPanel'
import FormFieldAgentPanel from './FormFieldAgentPanel'
import IndependentAgentPanel from './IndependentAgentPanel'
import SkillRulesPanel from './SkillRulesPanel'
import ReviewScoringPanel from './ReviewScoringPanel'
import AgentLlmRoutePanel from './AgentLlmRoutePanel'
import AgentRunsPanel from './AgentRunsPanel'

const AGENT_TABS = [
  { key: 'definitions', label: '独立 Agent', icon: Bot },
  { key: 'runs', label: '运行记录', icon: Activity },
  { key: 'catalog', label: '全景', icon: LayoutGrid },
  { key: 'form', label: '填表', icon: Sparkles },
  { key: 'rules', label: '规则', icon: BookOpen },
  { key: 'review', label: '质检', icon: Gauge },
  { key: 'routes', label: '路由', icon: Route },
]

export default function AgentHubPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'definitions'
  const active = AGENT_TABS.find((t) => t.key === tab) || AGENT_TABS[0]
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  const switchTab = (key) => {
    const next = new URLSearchParams(searchParams)
    next.set('tab', key)
    if (key !== 'form') next.delete('action')
    setSearchParams(next, { replace: true })
  }

  return (
    <AdminShell hideDescription>
      <AdminPageHeader
        crumbs={[{ label: 'Console' }, { label: 'Agent 中心' }]}
        title="独立 Agent · LLM 路由 · 评审评分"
        subtitle="独立 Agent 定义、Prompt、Knowledge 绑定与路由健康"
      />
      <AdminPillTabs tabs={AGENT_TABS} active={active.key} onChange={switchTab} className="w-full" />
      <MessageBanner />
      {active.key === 'definitions' ? <IndependentAgentPanel onMessage={showMessage} /> : null}
      {active.key === 'runs' ? <AgentRunsPanel /> : null}
      {active.key === 'catalog' ? (
        <AdminAgentCatalogPanel
          onSelectFormAgent={(actionKey) => {
            const next = new URLSearchParams(searchParams)
            next.set('tab', 'form')
            if (actionKey) next.set('action', actionKey)
            setSearchParams(next, { replace: true })
          }}
        />
      ) : null}
      {active.key === 'form' ? <FormFieldAgentPanel /> : null}
      {active.key === 'rules' ? <SkillRulesPanel onMessage={showMessage} /> : null}
      {active.key === 'review' ? <ReviewScoringPanel onMessage={showMessage} /> : null}
      {active.key === 'routes' ? <AgentLlmRoutePanel onMessage={showMessage} /> : null}
    </AdminShell>
  )
}
