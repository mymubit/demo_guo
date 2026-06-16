import AdminShell from '@/components/admin/AdminShell'
import SystemConfigPanel from '@/pages/Admin/system/SystemConfigPanel'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'

export function SystemAdvancedPage() {
  const { showMessage, MessageBanner } = useAdminPanelMessage()
  return (
    <AdminShell title="系统高级配置">
      <MessageBanner />
      <SystemConfigPanel onMessage={showMessage} />
    </AdminShell>
  )
}
