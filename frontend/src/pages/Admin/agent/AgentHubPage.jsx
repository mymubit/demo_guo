import { useSearchParams } from 'react-router-dom'
import { Bot, LayoutGrid, Sparkles, Gauge, Route, BookOpen } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminPageHeader, AdminPillTabs } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import AdminAgentCatalogPanel from './AdminAgentCatalogPanel'
import FormFieldAgentPanel from './FormFieldAgentPanel'
import AgentRegistryPanel from './AgentRegistryPanel'
import SkillRulesPanel from './SkillRulesPanel'
import ReviewScoringPanel from './ReviewScoringPanel'
import AgentLlmRoutePanel from './AgentLlmRoutePanel'

const AGENT_TABS = [
  { key: 'catalog', label: '全景', icon: LayoutGrid },
  { key: 'form', label: '填表', icon: Sparkles },
  { key: 'registry', label: '注册表', icon: Bot },
  { key: 'rules', label: '规则', icon: BookOpen },
  { key: 'review', label: '质检', icon: Gauge },
  { key: 'routes', label: '路由', icon: Route },
]

export default function AgentHubPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'catalog'
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
        title="Agent 注册表 · LLM 路由 · 评审评分"
        subtitle="全景、填表、注册表、规则、质检与路由"
      />
      <AdminPillTabs tabs={AGENT_TABS} active={active.key} onChange={switchTab} className="w-full" />
      <MessageBanner />
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
      {active.key === 'registry' ? <AgentRegistryPanel onMessage={showMessage} /> : null}
      {active.key === 'rules' ? <SkillRulesPanel onMessage={showMessage} /> : null}
      {active.key === 'review' ? <ReviewScoringPanel onMessage={showMessage} /> : null}
      {active.key === 'routes' ? <AgentLlmRoutePanel onMessage={showMessage} /> : null}
    </AdminShell>
  )
}
