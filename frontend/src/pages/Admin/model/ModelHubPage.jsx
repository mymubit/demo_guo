import AdminShell from '@/components/admin/AdminShell'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import LlmConfigPanel from './LlmConfigPanel'

export default function ModelHubPage() {
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  return (
    <AdminShell hideDescription>
      <MessageBanner />
      <LlmConfigPanel onMessage={showMessage} />
    </AdminShell>
  )
}
