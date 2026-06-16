import { Navigate, useSearchParams } from 'react-router-dom'
import { BookOpen, SlidersHorizontal } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminPageHeader, AdminPillTabs, AdminPanel } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import CreationFormPanel from './CreationFormPanel'
import HookLibraryPanel from './HookLibraryPanel'

const CONTENT_TABS = [
  {
    key: 'form',
    label: '创作页配置',
    icon: SlidersHorizontal,
    hint: '入口、题材、参数与表单文案；保存后用户刷新创作页即生效。',
  },
  {
    key: 'hooks',
    label: '钩子库',
    icon: BookOpen,
    hint: '短句模板库；主链生成时随机抽取已启用条目。',
  },
]

export default function PortalContentPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'form'

  if (tab === 'ai-fields') {
    const action = searchParams.get('action')
    const target = action
      ? `/admin/agent?tab=form&action=${encodeURIComponent(action)}`
      : '/admin/agent?tab=form'
    return <Navigate to={target} replace />
  }

  const active = CONTENT_TABS.find((t) => t.key === tab) || CONTENT_TABS[0]
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  const switchTab = (key) => {
    setSearchParams({ tab: key }, { replace: true })
  }

  return (
    <AdminShell hideDescription>
      <AdminPageHeader
        crumbs={[{ label: 'Console' }, { label: '门户内容' }]}
        title="门户题材 · 钩子库 · 创作表单"
        subtitle="创作页配置与钩子模板库"
      />
      <AdminPillTabs tabs={CONTENT_TABS} active={active.key} onChange={switchTab} className="w-full" />
      {active.hint ? (
        <p className="text-xs text-slate-500 leading-relaxed border-l-2 border-gold-500/25 pl-3">
          {active.hint}
        </p>
      ) : null}
      <MessageBanner />

      <AdminPanel>
        {tab === 'form' ? (
          <CreationFormPanel onMessage={showMessage} embedded />
        ) : (
          <HookLibraryPanel onMessage={showMessage} embedded />
        )}
      </AdminPanel>
    </AdminShell>
  )
}
