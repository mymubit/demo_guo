import AdminShell from '@/components/admin/AdminShell'
import BillingAdmin from '@/pages/Admin/Billing'

export function CommerceSettingsPage() {
  return (
    <AdminShell hideDescription title="商业·钱包">
      <BillingAdmin forcedTab="commerce" />
    </AdminShell>
  )
}
