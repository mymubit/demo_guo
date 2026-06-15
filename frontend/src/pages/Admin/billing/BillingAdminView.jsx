import { AdminLoading } from '@/components/admin/AdminUI'
import { useBilling } from './BillingContext.jsx'
import AiPromptsPanel from './AiPromptsPanel.jsx'
import CommerceSettingsPanel from './CommerceSettingsPanel.jsx'

export default function BillingAdminView() {
  const { forcedTab, loading } = useBilling()

  if (loading) {
    return <AdminLoading label="加载商业配置…" />
  }

  if (forcedTab === 'ai-prompts') {
    return <AiPromptsPanel />
  }

  if (forcedTab === 'commerce') {
    return <CommerceSettingsPanel />
  }

  return null
}
