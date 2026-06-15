import AdminShell from '@/components/admin/AdminShell'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import LlmConfigPanel from './LlmConfigPanel'

export default function ModelHubPage() {
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  return (
    <AdminShell
      title="模型中心"
      description="厂商 Key、模型目录、Token 单价与全局 LLM 设置"
    >
      <MessageBanner />
      <LlmConfigPanel onMessage={showMessage} />
    </AdminShell>
  )
}
