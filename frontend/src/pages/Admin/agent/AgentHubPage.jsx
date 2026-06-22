import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Bot, Route } from 'lucide-react'
import AiConfigShell from '@/components/admin/ai-config/AiConfigShell'
import { AdminPillTabs } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import IndependentAgentPanel from './IndependentAgentPanel'
import AgentLlmRoutePanel from './AgentLlmRoutePanel'
import AgentRunsPanel from './AgentRunsPanel'

/** Agent 定义页内子 Tab：运行记录由侧栏独立入口，此处仅保留定义与路由 */
const AGENT_DEFINITION_TABS = [
  { key: 'definitions', label: 'Prompt 定义', icon: Bot },
  { key: 'routes', label: 'LLM 路由', icon: Route },
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
  const isRunsPage = resolvedTab === 'runs'

  useEffect(() => {
    if (tab === 'rules') {
      navigate('/admin/tier-rules', { replace: true })
    }
  }, [tab, navigate])

  const { showMessage, MessageBanner } = useAdminPanelMessage()
  const sectionId = isRunsPage ? 'agent-runs' : 'agent-definitions'

  const switchTab = (key) => {
    const next = new URLSearchParams(searchParams)
    next.set('tab', key)
    next.delete('action')
    setSearchParams(next, { replace: true })
  }

  const definitionTab =
    AGENT_DEFINITION_TABS.find((t) => t.key === resolvedTab) || AGENT_DEFINITION_TABS[0]

  return (
    <AiConfigShell
      sectionId={sectionId}
      subTabs={
        isRunsPage ? null : (
          <AdminPillTabs
            tabs={AGENT_DEFINITION_TABS}
            active={definitionTab.key}
            onChange={switchTab}
            className="w-full"
          />
        )
      }
    >
      <MessageBanner />
      {isRunsPage ? <AgentRunsPanel /> : null}
      {!isRunsPage && definitionTab.key === 'definitions' ? (
        <IndependentAgentPanel onMessage={showMessage} />
      ) : null}
      {!isRunsPage && definitionTab.key === 'routes' ? (
        <AgentLlmRoutePanel onMessage={showMessage} />
      ) : null}
    </AiConfigShell>
  )
}
