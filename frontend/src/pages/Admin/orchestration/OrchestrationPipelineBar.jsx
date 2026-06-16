import { useMemo, useState } from 'react'
import { Copy, GitBranch, Star, Upload, Plus, Check } from 'lucide-react'
import { cn } from '@/utils/cn'

/** 流程编排顶栏：多流水线选择 / 复制 / 命名 / 发布 */
export default function OrchestrationPipelineBar({
  packs = [],
  activePackId = '',
  loading = false,
  busy = false,
  embedded = false,
  onSelectPack,
  onDuplicate,
  onUpdateMeta,
  onSetDefault,
  onTogglePublish,
}) {
  const [editingId, setEditingId] = useState('')
  const [draftName, setDraftName] = useState('')

  const activePack = useMemo(
    () => packs.find((p) => p.id === activePackId) || packs.find((p) => p.is_active) || packs[0],
    [packs, activePackId],
  )

  function startRename(pack) {
    setEditingId(pack.id)
    setDraftName(pack.display_name || pack.version || '')
  }

  async function commitRename(pack) {
    const name = draftName.trim()
    setEditingId('')
    if (!name || name === (pack.display_name || pack.version)) return
    await onUpdateMeta?.(pack.id, { display_name: name })
  }

  async function handleDuplicate() {
    if (!activePack) return
    const base = activePack.display_name || activePack.version || '流水线'
    await onDuplicate?.(activePack.id, `${base} 副本`)
  }

  const duplicateBtn = (
    <button
      type="button"
      disabled={busy || !activePack}
      onClick={handleDuplicate}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs border border-white/10 text-navy-200 hover:bg-white/[0.06] disabled:opacity-40"
    >
      <Copy className="w-3.5 h-3.5" />
      复制当前
    </button>
  )

  const packList = (
      <div className={embedded ? 'flex gap-2 overflow-x-auto pb-1' : 'mt-3 flex gap-2 overflow-x-auto pb-1'}>
        {(loading ? [] : packs).map((pack) => {
          const isActive = pack.is_active || pack.id === activePackId
          const isEditing = editingId === pack.id
          return (
            <div
              key={pack.id}
              className={cn(
                'shrink-0 min-w-[200px] max-w-[260px] rounded-xl border px-3 py-2.5 transition-all',
                isActive
                  ? 'border-gold-500/45 bg-gold-500/10'
                  : 'border-white/10 bg-white/[0.03] hover:border-white/20',
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <button
                  type="button"
                  disabled={busy || isActive}
                  onClick={() => onSelectPack?.(pack.id)}
                  className="text-left min-w-0 flex-1 disabled:cursor-default"
                >
                  {isEditing ? (
                    <input
                      value={draftName}
                      onChange={(e) => setDraftName(e.target.value)}
                      onBlur={() => commitRename(pack)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') commitRename(pack)
                        if (e.key === 'Escape') setEditingId('')
                      }}
                      autoFocus
                      className="sf-control px-2 py-0.5 text-sm"
                    />
                  ) : (
                    <div
                      className="text-sm font-medium text-white truncate"
                      title={pack.display_name || pack.version}
                      onDoubleClick={() => startRename(pack)}
                    >
                      {pack.display_name || pack.version}
                    </div>
                  )}
                  <div className="text-[11px] text-navy-400 mt-0.5 truncate">
                    {pack.node_count || 0} 步
                    {(pack.step_preview || []).length > 0
                      ? ` · ${(pack.step_preview || []).slice(0, 3).join(' → ')}`
                      : ''}
                  </div>
                </button>
                {isActive ? <Check className="w-4 h-4 text-gold-400 shrink-0 mt-0.5" /> : null}
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {pack.is_default_for_creation ? (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-300">默认</span>
                ) : (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onSetDefault?.(pack.id)}
                    className="text-[10px] px-1.5 py-0.5 rounded border border-white/10 text-navy-300 hover:text-white disabled:opacity-40 inline-flex items-center gap-0.5"
                  >
                    <Star className="w-2.5 h-2.5" />
                    设默认
                  </button>
                )}
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    onTogglePublish?.(pack.id, !pack.is_published_to_portal)
                  }
                  className={cn(
                    'text-[10px] px-1.5 py-0.5 rounded border inline-flex items-center gap-0.5 disabled:opacity-40',
                    pack.is_published_to_portal
                      ? 'border-green-500/35 text-green-300'
                      : 'border-white/10 text-navy-300 hover:text-white',
                  )}
                >
                  <Upload className="w-2.5 h-2.5" />
                  {pack.is_published_to_portal ? '已发布' : '发布入口'}
                </button>
              </div>
            </div>
          )
        })}
        {!loading && packs.length === 0 ? (
          <div className="text-xs text-navy-400 flex items-center gap-1.5 px-2">
            <Plus className="w-3.5 h-3.5" />
            暂无流水线，请先从 SSOT 导入
          </div>
        ) : null}
      </div>
  )

  if (embedded) {
    return (
      <div>
        <div className="mb-3 flex flex-wrap items-center justify-end gap-2">{duplicateBtn}</div>
        {packList}
      </div>
    )
  }

  return (
    <div className="sf-console-panel px-4 py-3 mb-4">
      <div className="flex flex-wrap items-center gap-3 justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <GitBranch className="w-4 h-4 text-gold-400 shrink-0" />
          <div>
            <h2 className="text-sm font-semibold text-white">流水线模板</h2>
            <p className="text-xs text-navy-400">选择要编辑的流水线 · 复制后可独立调整步骤与流程图</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">{duplicateBtn}</div>
      </div>
      {packList}
    </div>
  )
}
