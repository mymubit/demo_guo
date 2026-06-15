import AdminShell from '@/components/admin/AdminShell'
import AdminDashboardHints from '@/components/admin/AdminDashboardHints'
import AdminMembers from '@/pages/Admin/Members'

export function MembersPlansPage() {
  return (
    <AdminShell actions={<AdminDashboardHints scope="members" />}>
      <AdminMembers />
    </AdminShell>
  )
}
