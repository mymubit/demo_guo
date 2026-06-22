import { useLocation } from 'react-router-dom'
import AdminShell from '@/components/admin/AdminShell'
import { cn } from '@/utils/cn'
import {
  AI_CONFIG_SECTIONS,
  matchAiConfigSection,
} from './aiConfigSections'

/**
 * AI 配置区统一壳层：页标题 + 操作区 + 主内容
 * 分区切换仅由左侧栏负责，此处不再重复五 tab 导航
 */
export default function AiConfigShell({
  sectionId,
  actions,
  subTabs,
  children,
  className,
}) {
  const { pathname, search } = useLocation()
  const active =
    AI_CONFIG_SECTIONS.find((s) => s.id === sectionId) ||
    matchAiConfigSection(pathname, search) ||
    AI_CONFIG_SECTIONS[0]

  return (
    <AdminShell hideDescription>
      <div className={cn('space-y-4', className)}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-white tracking-tight">{active.label}</h1>
            <p className="mt-1 text-sm text-navy-400 max-w-3xl leading-relaxed">{active.description}</p>
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div> : null}
        </div>

        {subTabs ? <div>{subTabs}</div> : null}

        <div className="min-h-[calc(100vh-240px)]">{children}</div>
      </div>
    </AdminShell>
  )
}
