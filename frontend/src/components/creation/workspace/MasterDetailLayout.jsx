import { Save } from 'lucide-react'

export function MetaChip({ children, className = '' }) {
  return (
    <span
      className={`inline-flex items-center rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1 text-xs text-navy-100 ${className}`}
    >
      {children}
    </span>
  )
}

export function ContentSection({ title, subtitle, children, id, headerExtra }) {
  if (!children) return null
  return (
    <section id={id} className="border-b border-white/5 px-5 py-5 last:border-b-0">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h4 className="text-sm font-semibold text-white">{title}</h4>
        {subtitle && <span className="text-xs text-navy-400">{subtitle}</span>}
        {headerExtra}
      </div>
      {children}
    </section>
  )
}

export function AllContentShell({ meta, children, editMode, saving, onSave, showSave = true }) {
  return (
    <div className="space-y-4">
      {meta && <div className="flex flex-wrap items-center gap-2">{meta}</div>}
      <div className="overflow-hidden rounded-2xl border border-white/5 bg-slate-900/40">
        <div className="flex items-center justify-between gap-3 border-b border-white/5 bg-slate-900/60 px-5 py-3">
          <h4 className="text-sm font-semibold text-white">全部内容</h4>
          {editMode && showSave && onSave && (
            <button
              type="button"
              disabled={saving}
              onClick={onSave}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white transition-colors hover:bg-white/[0.06] disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              {saving ? '保存中…' : '保存'}
            </button>
          )}
        </div>
        <div className="max-h-[70vh] overflow-y-auto">{children}</div>
      </div>
    </div>
  )
}

export function PickerTile({ active, onClick, children, subtitle, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex aspect-square flex-col items-center justify-center gap-1 rounded-2xl border px-2 text-sm font-medium transition-all disabled:cursor-not-allowed disabled:opacity-40 ${
        active
          ? 'border-gold-400/50 bg-gold-400/10 text-white shadow-gold'
          : 'border-white/10 bg-white/[0.03] text-navy-300 hover:border-white/20 hover:text-white'
      }`}
    >
      <span className="line-clamp-3 w-full text-center leading-snug">{children}</span>
      {subtitle && (
        <span className="line-clamp-1 w-full text-center text-[10px] font-normal text-navy-400">
          {subtitle}
        </span>
      )}
    </button>
  )
}

export default function MasterDetailLayout({
  meta,
  detailTitle,
  detailExtra,
  detail,
  pickerLabel = '目录',
  picker,
  editMode,
  saving,
  onSave,
  showSave = true,
  emptyHint = '从右侧选择条目查看详情',
}) {
  return (
    <div className="space-y-4">
      {meta && <div className="flex flex-wrap items-center gap-2">{meta}</div>}

      <div className="flex flex-col-reverse gap-5 lg:flex-row lg:gap-6">
        <div className="min-w-0 flex-1 overflow-hidden rounded-2xl border border-white/5 bg-slate-900/40">
          <div className="flex items-center justify-between gap-3 border-b border-white/5 bg-slate-900/60 px-5 py-3">
            <div className="flex min-w-0 flex-wrap items-center gap-2">
              <h4 className="truncate text-sm font-semibold text-white">
                {detailTitle || '选择条目'}
              </h4>
              {detailExtra}
            </div>
            {editMode && showSave && onSave && (
              <button
                type="button"
                disabled={saving}
                onClick={onSave}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white transition-colors hover:bg-white/[0.06] disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                {saving ? '保存中…' : '保存'}
              </button>
            )}
          </div>
          <div className="max-h-[70vh] overflow-y-auto px-5 py-5">
            {detail || (
              <p className="py-8 text-center text-sm text-navy-400">{emptyHint}</p>
            )}
          </div>
        </div>

        <div className="w-full shrink-0 lg:w-64 xl:w-72">
          <div className="overflow-hidden rounded-2xl border border-white/5 bg-slate-900/40">
            <div className="border-b border-white/5 bg-slate-900/60 px-4 py-2.5">
              <div className="text-xs font-medium text-navy-300">{pickerLabel}</div>
            </div>
            <div className="max-h-[70vh] overflow-y-auto p-3">{picker}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
