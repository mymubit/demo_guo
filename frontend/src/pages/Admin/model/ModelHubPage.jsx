import AdminShell from '@/components/admin/AdminShell'
import { AdminPageHeader } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import LlmConfigPanel from './LlmConfigPanel'

export default function ModelHubPage() {
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  return (
    <AdminShell hideDescription>
      <AdminPageHeader
        crumbs={[{ label: 'Console' }, { label: 'AI 配置' }, { label: '大模型' }]}
        title="大模型配置"
        description="厂商凭证、模型接入、Token 单价与全局默认 Provider"
      />
      <MessageBanner />
      <LlmConfigPanel onMessage={showMessage} />
    </AdminShell>
  )
}
