import { findAdminNavItem } from '@/config/adminNav'
import { useLocation } from 'react-router-dom'
import { AdminPageHeader } from './AdminUI'

/**
 * 统一页面壳：标题/说明来自 adminNav，避免各页重复写 header
 */
export default function AdminShell({ title, description, actions, children, hideDescription = false }) {
  const { pathname } = useLocation()
  const nav = findAdminNavItem(pathname)

  return (
    <div className="space-y-6 w-full">
      <AdminPageHeader
        title={title || nav?.label || '管理后台'}
        description={hideDescription ? description : description || nav?.description}
        actions={actions}
      />
      {children}
    </div>
  )
}
