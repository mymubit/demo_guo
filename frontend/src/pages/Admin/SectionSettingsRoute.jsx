import AdminShell from '@/components/admin/AdminShell'
import SystemConfigPanel from '@/pages/Admin/system/SystemConfigPanel'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'

export function SystemAdvancedPage() {
  const { showMessage, MessageBanner } = useAdminPanelMessage()
  return (
    <AdminShell
      title="系统高级配置"
      description="引擎内部开关与默认值；大模型见「模型中心」，主链 Agent 见「Agent 中心」"
    >
      <MessageBanner />
      <SystemConfigPanel onMessage={showMessage} />
    </AdminShell>
  )
}
