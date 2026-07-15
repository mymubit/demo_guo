import { useMemo, useState } from 'react'
import { Tabs } from '@/components/ui/Tabs'
import { DELIVERY_TAB_ITEMS } from '@/config/workbench'
import { EmptyState } from '@/components/ui/Tabs'
import type { DeliveryItem } from '@/types/domain'

export function DeliveryTabs({
  packageData,
  enabledItems,
}: {
  packageData: Record<string, unknown> | null | undefined
  enabledItems: DeliveryItem[]
}) {
  const tabs = useMemo(
    () => DELIVERY_TAB_ITEMS.filter((t) => enabledItems.includes(t.id)),
    [enabledItems],
  )
  const [tab, setTab] = useState(tabs[0]?.id ?? 'storyboard')

  if (!packageData) {
    return <EmptyState title="暂无交付包" description="启用交付并完成 delivery 阶段后可在此查看。" />
  }

  const storyboard = (packageData.storyboard as unknown[]) ?? []
  const visual = (packageData.visual_assets as unknown[]) ?? []
  const marketing = (packageData.marketing_assets as unknown[]) ?? []
  const interactive = packageData.interactive_adaptation
  const production = packageData.production_plan as Record<string, unknown> | undefined
  const release = packageData.release_checklist as Record<string, unknown> | undefined

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-ink">交付包</h3>
      <Tabs items={tabs.map((t) => ({ id: t.id, label: t.label }))} value={tab} onChange={(id) => setTab(id as DeliveryItem)} />
      <div className="sf-panel p-4">
        {tab === 'storyboard' && <JsonList title="分镜" items={storyboard} />}
        {tab === 'visual' && <JsonList title="视觉资产" items={visual} />}
        {tab === 'marketing' && <JsonList title="宣发资产" items={marketing} />}
        {tab === 'interactive' && (
          <pre className="overflow-auto text-xs text-ink-muted">
            {interactive ? JSON.stringify(interactive, null, 2) : '无互动改编内容'}
          </pre>
        )}
        {tab === 'budget' && (
          <div className="space-y-2 text-sm">
            <p>复杂度：{String(production?.complexity_band ?? '—')}（{String(production?.complexity_score ?? '—')}）</p>
            <p>成本驱动：{Array.isArray(production?.cost_drivers) ? production?.cost_drivers.join('、') : '—'}</p>
            <pre className="overflow-auto rounded bg-canvas p-3 text-xs">
              {JSON.stringify(production?.budget_range ?? production ?? {}, null, 2)}
            </pre>
          </div>
        )}
        {tab === 'release' && (
          <div className="space-y-2 text-sm">
            <p>平台：{String(release?.target_platform ?? '—')}</p>
            <p>可上架：{String(release?.can_release ?? '—')}</p>
            <p>阻断项：{Array.isArray(release?.blocking_items) ? release?.blocking_items.join('、') || '无' : '—'}</p>
            <p>缺失材料：{Array.isArray(release?.missing_materials) ? release?.missing_materials.join('、') || '无' : '—'}</p>
          </div>
        )}
      </div>
    </div>
  )
}

function JsonList({ title, items }: { title: string; items: unknown[] }) {
  if (items.length === 0) return <p className="text-sm text-ink-muted">{title}为空</p>
  return (
    <ul className="space-y-2">
      {items.map((item, idx) => (
        <li key={idx} className="rounded-lg bg-canvas p-3 text-xs text-ink-muted">
          <pre className="whitespace-pre-wrap">{JSON.stringify(item, null, 2)}</pre>
        </li>
      ))}
    </ul>
  )
}
