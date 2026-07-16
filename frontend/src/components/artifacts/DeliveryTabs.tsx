import { useMemo, useState } from 'react'
import { Tabs } from '@/components/ui/Tabs'
import { EmptyState } from '@/components/ui/Tabs'
import { useWorkbenchDefinition } from '@/hooks/useWorkbenchDefinition'
import type { DeliveryItem } from '@/types/domain'

export function DeliveryTabs({
  packageData,
  enabledItems,
}: {
  packageData: Record<string, unknown> | null | undefined
  enabledItems: DeliveryItem[]
}) {
  const { definition } = useWorkbenchDefinition()
  const tabs = useMemo(
    () => definition.delivery_tab_items.filter((t) => enabledItems.includes(t.id as DeliveryItem)),
    [definition.delivery_tab_items, enabledItems],
  )
  const [tab, setTab] = useState(tabs[0]?.id ?? 'storyboard')

  if (!packageData) {
    return (
      <EmptyState
        title="暂无交付包"
        description="请先在创作设定中启用交付项，并完成「制作发行交付」阶段。"
      />
    )
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
      <Tabs
        items={tabs.map((t) => ({ id: t.id, label: t.label }))}
        value={tab}
        onChange={(id) => setTab(id)}
      />
      <div className="sf-panel p-4">
        {tab === 'storyboard' && <ObjectList title="分镜" items={storyboard} />}
        {tab === 'visual' && <ObjectList title="视觉资产" items={visual} />}
        {tab === 'marketing' && <ObjectList title="宣发资产" items={marketing} />}
        {tab === 'interactive' &&
          (interactive && typeof interactive === 'object' ? (
            <KeyCards data={interactive as Record<string, unknown>} />
          ) : (
            <p className="text-sm text-ink-muted">无互动改编内容</p>
          ))}
        {tab === 'budget' && (
          <div className="space-y-2 text-sm">
            <p>
              复杂度：{String(production?.complexity_band ?? '—')}（
              {String(production?.complexity_score ?? '—')}）
            </p>
            <p>
              成本驱动：
              {Array.isArray(production?.cost_drivers) ? production?.cost_drivers.join('、') : '—'}
            </p>
            {production?.budget_range && typeof production.budget_range === 'object' ? (
              <KeyCards data={production.budget_range as Record<string, unknown>} />
            ) : production ? (
              <KeyCards data={production} />
            ) : (
              <p className="text-ink-muted">暂无预算明细</p>
            )}
          </div>
        )}
        {tab === 'release' && (
          <div className="space-y-2 text-sm">
            <p>平台：{String(release?.target_platform ?? '—')}</p>
            <p>可上架：{String(release?.can_release ?? '—')}</p>
            <p>
              阻断项：
              {Array.isArray(release?.blocking_items)
                ? release?.blocking_items.join('、') || '无'
                : '—'}
            </p>
            <p>
              缺失材料：
              {Array.isArray(release?.missing_materials)
                ? release?.missing_materials.join('、') || '无'
                : '—'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function ObjectList({ title, items }: { title: string; items: unknown[] }) {
  if (items.length === 0) return <p className="text-sm text-ink-muted">{title}为空</p>
  return (
    <ul className="space-y-2">
      {items.map((item, idx) => (
        <li key={idx} className="rounded-lg bg-canvas p-3 text-sm text-ink">
          {item && typeof item === 'object' && !Array.isArray(item) ? (
            <KeyCards data={item as Record<string, unknown>} compact />
          ) : (
            <span className="text-ink-muted">{String(item)}</span>
          )}
        </li>
      ))}
    </ul>
  )
}

function KeyCards({ data, compact }: { data: Record<string, unknown>; compact?: boolean }) {
  const entries = Object.entries(data)
  if (entries.length === 0) return <p className="text-sm text-ink-muted">暂无内容</p>
  return (
    <dl className={compact ? 'grid gap-2 sm:grid-cols-2' : 'grid gap-3 sm:grid-cols-2'}>
      {entries.map(([key, value]) => (
        <div key={key} className={compact ? '' : 'rounded-md bg-canvas p-2'}>
          <dt className="text-xs text-ink-faint">{key}</dt>
          <dd className="mt-0.5 whitespace-pre-wrap text-sm text-ink">
            {typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
              ? String(value)
              : Array.isArray(value)
                ? value.map((v) => (typeof v === 'string' ? v : JSON.stringify(v))).join('、') || '—'
                : value && typeof value === 'object'
                  ? JSON.stringify(value)
                  : '—'}
          </dd>
        </div>
      ))}
    </dl>
  )
}
