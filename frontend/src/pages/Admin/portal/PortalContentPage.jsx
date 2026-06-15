import { Link, useSearchParams } from 'react-router-dom'
import { BookOpen, SlidersHorizontal, Sparkles } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminTabBar } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import CreationFormPanel from './CreationFormPanel'
import HookLibraryPanel from './HookLibraryPanel'
import BillingAdmin from '@/pages/Admin/billing'

const CONTENT_TABS = [
  {
    key: 'form',
    label: '创作页配置',
    icon: SlidersHorizontal,
    hint: '决定用户在「发起创作」页看到什么：入口、题材、参数与表单文案。保存后用户刷新即生效。',
  },
  {
    key: 'ai-fields',
    label: '填表 AI',
    icon: Sparkles,
    hint: '创作页字段级 AI 生成：提示词、单次扣费与模型绑定。',
  },
  {
    key: 'hooks',
    label: '钩子库',
    icon: BookOpen,
    hint: '短句模板库。主链生成大纲/剧本时会随机抽取「已启用」的条目，用户不会在表单里看到这些文案。',
  },
]

export default function PortalContentPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'form'
  const active = CONTENT_TABS.find((t) => t.key === tab) || CONTENT_TABS[0]
  const { showMessage, MessageBanner } = useAdminPanelMessage()

  const switchTab = (key) => {
    setSearchParams({ tab: key }, { replace: true })
  }

  return (
    <AdminShell
      title="配置中心"
      description="C 端展示与素材：创作页表单 · 主链引用的钩子短句"
    >
      <div className="glass-card rounded-2xl p-5 border border-navy-700/30">
        <p className="text-sm text-navy-200 leading-relaxed">
          这里管的是<strong className="text-white">用户侧展示与素材</strong>，不是 Agent 提示词或扣费。
          改提示词、模型、主链步骤请分别前往
          <Link to="/admin/agent" className="text-gold-400 hover:underline mx-1">
            Agent 中心
          </Link>
          、
          <Link to="/admin/model" className="text-gold-400 hover:underline mx-1">
            模型中心
          </Link>
          与
          <Link to="/admin/main-chain" className="text-gold-400 hover:underline mx-1">
            主链工作室
          </Link>
          。
        </p>
      </div>

      <AdminTabBar tabs={CONTENT_TABS} active={active.key} onChange={switchTab} stretch />
      <p className="text-sm text-navy-400">{active.hint}</p>
      <MessageBanner />

      {tab === 'form' ? (
        <CreationFormPanel onMessage={showMessage} embedded />
      ) : tab === 'ai-fields' ? (
        <BillingAdmin forcedTab="ai-prompts" />
      ) : (
        <HookLibraryPanel onMessage={showMessage} embedded />
      )}
    </AdminShell>
  )
}
