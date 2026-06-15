import AdminShell from '@/components/admin/AdminShell'
import BillingAdmin from '@/pages/Admin/Billing'

export function CommerceSettingsPage() {
  return (
    <AdminShell title="商业·钱包" description="人民币充值档位与站内创作币规则；LLM API 成本见 Dashboard「大模型成本」">
      <BillingAdmin forcedTab="commerce" />
    </AdminShell>
  )
}
