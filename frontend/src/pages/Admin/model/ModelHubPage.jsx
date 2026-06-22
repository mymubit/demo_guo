import AiConfigShell from '@/components/admin/ai-config/AiConfigShell'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import LlmConfigPanel from './LlmConfigPanel'

export default function ModelHubPage() {
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  return (
    <AiConfigShell sectionId="model">
      <MessageBanner />
      <LlmConfigPanel onMessage={showMessage} />
    </AiConfigShell>
  )
}
