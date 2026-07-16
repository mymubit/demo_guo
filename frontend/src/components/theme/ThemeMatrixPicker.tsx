import { useMemo, useState } from 'react'
import { Check, Search, Sparkles } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { ThemeMatrix } from '@/types/workbench'
import type { GenreMatrix } from '@/types/domain'

type Props = {
  matrix: ThemeMatrix
  genreMatrix: Partial<GenreMatrix>
  flavorTags: string[]
  presetThemeCode?: string | null
  onChangeGenre: (next: Partial<GenreMatrix>) => void
  onChangeFlavorTags: (tags: string[]) => void
  onChangePreset?: (code: string | null) => void
}

/** 借鉴「点选即填」交互，视觉保持本站浅色面板 */

export function ThemeMatrixPicker({
  matrix,
  genreMatrix,
  flavorTags,
  presetThemeCode,
  onChangeGenre,
  onChangeFlavorTags,
  onChangePreset,
}: Props) {
  const [comboSearch, setComboSearch] = useState('')
  const [flavorFilter, setFlavorFilter] = useState('')
  const maxSelect = matrix.flavor_tags.max_select ?? 5
  const dimOrder = matrix.dim_order ?? ['emotion', 'identity', 'conflict', 'world']

  const combos = useMemo(() => {
    const list = matrix.featured_combos ?? []
    const q = comboSearch.trim().toLowerCase()
    if (!q) return list.slice(0, 8)
    return list.filter((c) => {
      const label = (c.label_zh || c.label || c.code || '').toLowerCase()
      return label.includes(q) || c.code.toLowerCase().includes(q)
    })
  }, [matrix.featured_combos, comboSearch])

  const flavorGroups = useMemo(() => {
    const q = flavorFilter.trim().toLowerCase()
    return (matrix.flavor_tags.categories ?? [])
      .map((cat) => {
        const options = (matrix.flavor_tags.options ?? []).filter((o) => {
          if (o.category !== cat.id) return false
          if (!q) return true
          return o.label_zh.toLowerCase().includes(q) || o.value.toLowerCase().includes(q)
        })
        return { ...cat, options }
      })
      .filter((g) => g.options.length > 0)
  }, [matrix, flavorFilter])

  function toggleFlavor(tag: string) {
    if (flavorTags.includes(tag)) {
      onChangeFlavorTags(flavorTags.filter((t) => t !== tag))
      return
    }
    if (flavorTags.length >= maxSelect) return
    onChangeFlavorTags([...flavorTags, tag])
  }

  const summary = dimOrder
    .map((axis) => {
      const value = genreMatrix[axis as keyof GenreMatrix]
      if (!value) return null
      return matrix.axes[axis]?.options.find((o) => o.value === value)?.label_zh ?? value
    })
    .filter(Boolean)

  return (
    <div className="space-y-6">
      {summary.length > 0 ? (
        <div className="rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
          <span className="font-medium">当前组合：</span>
          {summary.join(' × ')}
          {flavorTags.length > 0 ? ` · ${flavorTags.length} 个标签` : ''}
        </div>
      ) : (
        <p className="text-sm text-ink-muted">先点选下方轴心，或从热门组合一键填入。</p>
      )}

      <section className="space-y-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-ink">
          <Sparkles className="h-4 w-4 text-gold-400" />
          热门组合
        </div>
        {(matrix.featured_combos?.length ?? 0) === 0 ? (
          <p className="text-sm text-ink-muted">暂无热门组合，请直接点选四轴。</p>
        ) : (
          <>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
              <input
                className="sf-control pl-9"
                value={comboSearch}
                onChange={(e) => setComboSearch(e.target.value)}
                placeholder="搜索热门组合…"
              />
            </div>
            <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
              {combos.map((combo) => {
                const active = presetThemeCode === combo.code
                return (
                  <button
                    key={combo.code}
                    type="button"
                    onClick={() => {
                      onChangeGenre({
                        emotion: combo.emotion,
                        identity: combo.identity,
                        conflict: combo.conflict,
                        world: combo.world,
                      })
                      if (combo.flavor_tags) {
                        onChangeFlavorTags(combo.flavor_tags.slice(0, maxSelect))
                      }
                      onChangePreset?.(combo.code)
                    }}
                    className={cn(
                      'rounded-lg border px-3 py-2.5 text-left text-sm transition',
                      active
                        ? 'border-gold-400 bg-amber-50'
                        : 'border-slate-200 bg-white hover:border-brand-300',
                    )}
                  >
                    <div className="flex items-center justify-between gap-1">
                      <span className="line-clamp-1 font-medium text-ink">
                        {combo.label_zh || combo.label || combo.code}
                      </span>
                      {active ? <Check className="h-3.5 w-3.5 shrink-0 text-gold-500" /> : null}
                    </div>
                  </button>
                )
              })}
            </div>
          </>
        )}
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {dimOrder.map((axisKey) => {
          const axis = matrix.axes[axisKey]
          if (!axis) return null
          const selected = genreMatrix[axisKey as keyof GenreMatrix]
          return (
            <div key={axisKey} className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
              <h4 className="text-sm font-semibold text-ink">{axis.label_zh}</h4>
              {axis.hint ? <p className="mt-1 text-xs text-ink-muted">{axis.hint}</p> : null}
              <div className="mt-3 grid grid-cols-2 gap-2">
                {axis.options.map((opt) => {
                  const isSelected = selected === opt.value
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => {
                        onChangeGenre({ ...genreMatrix, [axisKey]: opt.value })
                        onChangePreset?.(null)
                      }}
                      className={cn(
                        'rounded-lg border px-2.5 py-2 text-left transition',
                        isSelected
                          ? 'border-brand-500 bg-brand-50 text-brand-700'
                          : 'border-slate-200 bg-white hover:border-slate-300',
                      )}
                    >
                      <div className="text-sm font-medium">{opt.label_zh}</div>
                      {opt.desc ? (
                        <div className="mt-0.5 line-clamp-2 text-[11px] text-ink-muted">
                          {opt.desc}
                        </div>
                      ) : null}
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-ink">
            风味标签
            <span className="ml-2 font-normal text-ink-muted">
              {flavorTags.length}/{maxSelect}
            </span>
          </h4>
          <button
            type="button"
            className="text-xs text-ink-muted hover:text-brand-600"
            onClick={() => onChangeFlavorTags([])}
          >
            清空
          </button>
        </div>
        <input
          className="sf-control"
          value={flavorFilter}
          onChange={(e) => setFlavorFilter(e.target.value)}
          placeholder="筛选标签…"
        />
        <div className="space-y-3">
          {flavorGroups.map((group) => (
            <div key={group.id}>
              <div className="mb-2 text-xs font-medium text-ink-faint">{group.label_zh}</div>
              <div className="flex flex-wrap gap-2">
                {group.options.map((opt) => {
                  const active = flavorTags.includes(opt.value)
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => toggleFlavor(opt.value)}
                      className={cn(
                        'rounded-full border px-3 py-1 text-xs transition',
                        active
                          ? 'border-brand-500 bg-brand-500 text-white'
                          : 'border-slate-200 bg-white text-ink-muted hover:border-brand-300',
                      )}
                    >
                      {opt.label_zh}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
